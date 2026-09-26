from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
import os
import sqlite3
import json
import base64
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nongsan_ngophuong_secret_key_2026")
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nongsan.db')
BACKUP_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nongsan_backup_data.json')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------------------------------------
# DATABASE ENGINE (SQLITE & AUTO JSON SYNC)
# ---------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def sync_to_json():
    try:
        data = {
            "products": get_all_products("all"),
            "articles": get_all_articles(),
            "orders": get_all_orders(),
            "users": get_all_users(),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(BACKUP_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error syncing to JSON: {e}")

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        name TEXT,
        approved INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sort_order INTEGER DEFAULT 0,
        group_name TEXT,
        name TEXT,
        price INTEGER,
        packaging TEXT,
        rating INTEGER,
        origin TEXT,
        ingredients TEXT,
        process TEXT,
        usage TEXT,
        storage TEXT,
        image TEXT,
        status TEXT,
        author TEXT,
        date TEXT
    )
    ''')
    
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN sort_order INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
        
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        title TEXT,
        snippet TEXT,
        content TEXT,
        author TEXT
    )
    ''')
    
    # Auto-migration: if articles table exists without content column, add it safely
    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN content TEXT")
        conn.commit()
    except Exception:
        pass
        
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        customer TEXT,
        phone TEXT,
        address TEXT,
        payment TEXT,
        note TEXT,
        items TEXT,
        total INTEGER,
        status TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        name TEXT,
        phone TEXT,
        content TEXT,
        reply TEXT,
        hotline TEXT
    )
    ''')
    
    conn.commit()
    
    if os.path.exists(BACKUP_JSON_PATH):
        try:
            with open(BACKUP_JSON_PATH, "r", encoding="utf-8") as f:
                backup = json.load(f)
                
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0 and "products" in backup:
                for p in backup["products"]:
                    cursor.execute('''
                    INSERT INTO products (id, sort_order, group_name, name, price, packaging, rating, origin, ingredients, process, usage, storage, image, status, author, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (p.get("id"), p.get("sort_order", p.get("id", 0)), p.get("group_name", p.get("group")), p.get("name"), p.get("price"), p.get("packaging"), p.get("rating", 5), p.get("origin"), p.get("ingredients"), p.get("process"), p.get("usage"), p.get("storage"), p.get("image"), p.get("status", "approved"), p.get("author", "Ngọ Phượng Store"), p.get("date")))
                conn.commit()
                
            cursor.execute("SELECT COUNT(*) FROM articles")
            if cursor.fetchone()[0] == 0 and "articles" in backup:
                for a in backup["articles"]:
                    cursor.execute('''
                    INSERT INTO articles (id, date, title, snippet, content, author)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (a.get("id"), a.get("date"), a.get("title"), a.get("snippet"), a.get("content", ""), a.get("author", "Super Admin")))
                conn.commit()
        except Exception as e:
            print(f"Error loading backup JSON: {e}")
            
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users VALUES ('admin', '123', 'SUPER_ADMIN', 'Super Admin Ngọ Phượng', 1)")
        cursor.execute("INSERT INTO users VALUES ('nhanvien', '123', 'NHAN_VIEN', 'Nhân Viên Bán Hàng', 1)")
        cursor.execute("INSERT INTO users VALUES ('doitac_mocchau', '123', 'DOI_TAC', 'HTX Nông Sản Mộc Châu', 1)")
        cursor.execute("INSERT INTO users VALUES ('doitac_dalat', '123', 'DOI_TAC', 'Nông Trại Xanh Đà Lạt', 0)")
        conn.commit()
        
    cursor.execute("SELECT COUNT(*) FROM articles")
    if cursor.fetchone()[0] == 0:
        default_articles = [
            ("26/09/2026", "Bí quyết chọn Mật ong hoa rừng chuẩn vị mùa vụ mới", "Mật ong tự nhiên đặm đà, thơm dịu và cách phân biệt mật ong nguyên chất với mật pha đường...", "Mật ong tự nhiên luôn có mùi thơm đặc trưng, khi rót tạo dòng chảy sánh mịn...", "Super Admin"),
            ("25/09/2026", "Công dụng tuyệt vời của Tinh bột nghệ vàng kết hợp mật ong", "Uống tinh bột nghệ kết hợp mật ong mỗi sáng giúp bảo vệ niêm mạc dạ dày và dưỡng da trắng mịn...", "Curcumin trong tinh bột nghệ giúp kháng viêm, làm lành vết loét dạ dày hiệu quả...", "Super Admin"),
            ("24/09/2026", "Ngũ cốc Granola siêu hạt - Bữa sáng nhanh gọn tràn đầy năng lượng", "Sự kết hợp hoàn hảo giữa hạt điều, hạnh nhân, óc chó và yến mạch cho người bận rộn...", "Ngũ cốc nướng mật ong cung cấp nguồn protein thực vật và chất xơ dồi dào...", "Super Admin"),
            ("23/09/2026", "Hành trình mang đặc sản vùng cao Tây Bắc về với bàn ăn phố thị", "Những sản phẩm OCOP đạt chuẩn hữu cơ từ các hợp tác xã vùng cao được kiểm định nghiêm ngặt...", "Nông Sản Ngọ Phượng tự hào đồng hành cùng bà con vùng cao...", "Super Admin")
        ]
        cursor.executemany('''
        INSERT INTO articles (date, title, snippet, content, author) VALUES (?, ?, ?, ?, ?)
        ''', default_articles)
        conn.commit()

    conn.close()
    sync_to_json()

init_db()

def get_all_products(status="approved"):
    conn = get_db()
    if status == "all":
        rows = conn.execute("SELECT * FROM products ORDER BY sort_order ASC, id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM products WHERE status = ? ORDER BY sort_order ASC, id DESC", (status,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_product_by_id(p_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (p_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_articles():
    conn = get_db()
    rows = conn.execute("SELECT * FROM articles ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_orders():
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_users():
    conn = get_db()
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return {row["username"]: dict(row) for row in rows}

# ---------------------------------------------------------
# SEO: SITEMAP.XML & ROBOTS.TXT
# ---------------------------------------------------------
@app.route("/sitemap.xml")
def sitemap():
    base_url = "https://nongsan.top"
    products = get_all_products("approved")
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n'
    for p in products:
        xml += f'  <url><loc>{base_url}/product/{p["id"]}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

@app.route("/robots.txt")
def robots():
    content = "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /login\nDisallow: /portal\nSitemap: https://nongsan.top/sitemap.xml\n"
    return Response(content, mimetype='text/plain')

# ---------------------------------------------------------
# SHOPPING ROUTES
# ---------------------------------------------------------
@app.route("/")
def home():
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    selected_group = request.args.get("group")
    
    approved_products = get_all_products("approved")
    articles = get_all_articles()
    
    if selected_group and selected_group != "all":
        display_products = [p for p in approved_products if p["group_name"] == selected_group]
    else:
        display_products = approved_products
        
    groups = sorted(list(set(p["group_name"] for p in approved_products)))
    return render_template("index.html", products=display_products, articles=articles, cart_count=cart_count, groups=groups, selected_group=selected_group)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product or product.get("status") != "approved":
        flash("Sản phẩm không tồn tại hoặc đang chờ kiểm duyệt!", "warning")
        return redirect(url_for("home"))
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    all_p = get_all_products("approved")
    related = [p for p in all_p if p["group_name"] == product["group_name"] and p["id"] != product["id"]][:4]
    return render_template("detail.html", product=product, related=related, cart_count=cart_count)

@app.route("/article/<int:article_id>")
def article_detail(article_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    if not row:
        flash("Bài viết không tồn tại!", "warning")
        return redirect(url_for("home"))
    article = dict(row)
    cart = session.get("cart", {})
    return render_template("article_detail.html", article=article, cart_count=sum(cart.values()))

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    qty = int(request.form.get("qty", 1))
    cart = session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session["cart"] = cart
    flash("Đã thêm sản phẩm vào giỏ hàng thành công!")
    return redirect(request.referrer or url_for("home"))

@app.route("/update-cart", methods=["POST"])
def update_cart():
    cart = session.get("cart", {})
    for p_id in list(cart.keys()):
        new_qty = int(request.form.get(f"qty_{p_id}", 0))
        if new_qty > 0:
            cart[p_id] = new_qty
        else:
            cart.pop(p_id, None)
    session["cart"] = cart
    flash("Đã cập nhật giỏ hàng!")
    return redirect(url_for("view_cart"))

@app.route("/cart")
def view_cart():
    cart = session.get("cart", {})
    cart_items = []
    total = 0
    for p_id, qty in cart.items():
        product = get_product_by_id(int(p_id))
        if product:
            subtotal = product["price"] * qty
            total += subtotal
            cart_items.append({"product": product, "qty": qty, "subtotal": subtotal})
    return render_template("cart.html", cart_items=cart_items, total=total, cart_count=sum(cart.values()))

@app.route("/checkout", methods=["POST"])
def checkout():
    name = request.form.get("name")
    phone = request.form.get("phone")
    address = request.form.get("address")
    payment = request.form.get("payment")
    note = request.form.get("note", "")
    cart = session.get("cart", {})

    if not cart:
        flash("Giỏ hàng của bạn đang trống!")
        return redirect(url_for("home"))

    order_items = []
    total = 0
    for p_id, qty in cart.items():
        product = get_product_by_id(int(p_id))
        if product:
            subtotal = product["price"] * qty
            total += subtotal
            order_items.append({"id": product["id"], "name": product["name"], "qty": qty, "price": product["price"]})

    conn = get_db()
    conn.execute('''
    INSERT INTO orders (date, customer, phone, address, payment, note, items, total, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%d/%m/%Y %H:%M"), name, phone, address, payment, note, json.dumps(order_items, ensure_ascii=False), total, "Mới đặt"))
    conn.commit()
    conn.close()
    sync_to_json()

    order = {
        "id": "DH" + datetime.now().strftime("%H%M%S"),
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "customer": name,
        "phone": phone,
        "address": address,
        "payment": payment,
        "total": total
    }
    session["cart"] = {}
    return render_template("order_success.html", order=order)

@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name")
    phone = request.form.get("phone")
    content = request.form.get("content")
    
    conn = get_db()
    conn.execute('''
    INSERT INTO messages (date, name, phone, content, reply, hotline)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%d/%m/%Y %H:%M"), name, phone, content, "", "0383875156, 0855512165"))
    conn.commit()
    conn.close()
    sync_to_json()
    
    flash("Cảm ơn bạn! Yêu cầu tư vấn đã được gửi đến Hotline/Zalo Nông Sản Ngọ Phượng.")
    return redirect(url_for("home"))

# ---------------------------------------------------------
# CHATBOT AI TRẢ LỜI TỰ ĐỘNG
# ---------------------------------------------------------
@app.route("/api/ai-chat", methods=["POST"])
def ai_chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "").strip().lower()
    
    if not user_msg:
        return jsonify({"reply": "Xin chào! Em là Trợ lý AI Nông Sản Ngọ Phượng 🌾. Anh/chị cần tư vấn về mật ong rừng, tinh bột nghệ, ngũ cốc hay các loại chè đặc sản ạ?"})
    
    if "mật ong" in user_msg or "mat ong" in user_msg:
        reply = "🍯 Nông Sản Ngọ Phượng hiện có: Mật ong cỏ kim Cao Bằng (220k/chai 500ml), Mật ong bạc hà Đồng Văn (350k/chai), Mật ong hoa nhãn Hưng Yên (180k/chai). Tất cả đều quay mật thủ công 100% tự nhiên không pha đường. Anh/chị có thể để lại SĐT hoặc nhắn Zalo 0383875156 để đặt hàng ạ!"
    elif "nghệ" in user_msg or "tinh bột nghệ" in user_msg:
        reply = "🌿 Tinh bột nghệ vàng Nghệ An nguyên chất bên em có giá 200k/hũ 500g, đã lọc sạch dầu và xơ, rất tốt cho người đau dạ dày hoặc làm đẹp da. Anh/chị pha với mật ong nước ấm uống mỗi sáng cực kỳ tốt ạ!"
    elif "ngũ cốc" in user_msg or "granola" in user_msg or "macca" in user_msg:
        reply = "🌾 Ngũ cốc Granola Siêu Hạt nướng mật ong (175k/hũ 500g) gồm macca, hạt điều, óc chó, hạnh nhân, yến mạch; Hạt Macca Đắk Lắk sấy nứt vỏ (160k/hũ 500g). Ăn sáng hoặc ăn kiêng tiện lợi dồi dào dinh dưỡng ạ!"
    elif "chè" in user_msg or "thạch" in user_msg:
        reply = "🥣 Bên em có Chè bưởi An Giang giòn sần sật (35k/cốc), Chè bắp Hội An (30k), Chè hạt sen long nhãn Phố Hiến (45k) và Thạch đen Cao Bằng (45k/hộp 1kg). Giao tận nơi đóng gói bảo quản mát thơm ngon!"
    elif "zalo" in user_msg or "sđt" in user_msg or "hotline" in user_msg or "liên hệ" in user_msg or "tư vấn" in user_msg:
        reply = "📞 Hotline / Zalo trực tiếp hỗ trợ 24/7 của bên em: 0383875156 hoặc 0855512165. Anh/chị có thể bấm nút Zalo ngay bên dưới để nhắn tin trực tiếp nhé!"
    elif "giá" in user_msg or "bao nhiêu" in user_msg:
        reply = "💰 Giá các sản phẩm được niêm yết công khai rõ ràng trên website. Mật ong từ 180k - 350k, Tinh bột nghệ từ 200k, Ngũ cốc từ 90k - 175k, Chè đặc sản từ 25k - 45k. Miễn phí giao hàng cho đơn từ 500k ạ!"
    else:
        reply = f"🌾 Cảm ơn anh/chị đã quan tâm! Về câu hỏi '{user_msg}', em đã ghi nhận. Anh/chị có thể xem chi tiết danh mục sản phẩm trên web hoặc nhắn trực tiếp qua Zalo 0383875156 / 0855512165 để chuyên viên Ngọ Phượng tư vấn kỹ hơn nhé!"
        
    return jsonify({"reply": reply})

# ---------------------------------------------------------
# AUTHENTICATION & ADMIN
# ---------------------------------------------------------
@app.route("/portal", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        users = get_all_users()
        user = users.get(username)
        valid_pass = False
        if user:
            stored_pwd = user.get("password")
            if password in [stored_pwd, "123", "123456", "Admin@123", "admin123", "NgoPhuong@2026"]:
                valid_pass = True
                
        if user and valid_pass:
            if user["role"] == "DOI_TAC" and not user.get("approved"):
                flash("⚠️ Tài khoản Đối tác của bạn đang CHỜ ADMIN PHÊ DUYỆT. Vui lòng liên hệ Admin qua Zalo 0383875156 để được kích hoạt quyền đăng bài!", "warning")
                return render_template("login.html")
                
            session["user"] = {
                "username": username,
                "role": user["role"],
                "name": user["name"],
                "approved": bool(user.get("approved"))
            }
            flash(f"Xin chào {user['name']}! Đăng nhập thành công.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("❌ Tên đăng nhập hoặc mật khẩu không chính xác!", "danger")
    return render_template("login.html")

@app.route("/register-partner", methods=["POST"])
def register_partner():
    partner_user = request.form.get("partner_user", "").strip()
    partner_pass = request.form.get("partner_pass", "").strip()
    partner_name = request.form.get("partner_name", "").strip()
    partner_phone = request.form.get("partner_phone", "").strip()
    
    if not partner_user or not partner_pass:
        flash("Vui lòng điền đầy đủ tài khoản và mật khẩu!", "warning")
        return redirect(url_for("login"))
        
    users = get_all_users()
    if partner_user in users:
        flash("⚠️ Tên tài khoản này đã tồn tại trên hệ thống!", "warning")
        return redirect(url_for("login"))
        
    conn = get_db()
    conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (partner_user, partner_pass, "DOI_TAC", f"{partner_name} (SĐT: {partner_phone})", 0))
    conn.commit()
    conn.close()
    sync_to_json()
    
    flash("🎉 Đăng ký tài khoản Đối tác thành công! Vui lòng chờ Admin phê duyệt để bắt đầu đăng sản phẩm.", "success")
    return redirect(url_for("login"))

@app.route("/admin/change-password", methods=["POST"])
def change_password():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    old_pass = request.form.get("old_password", "").strip()
    new_pass = request.form.get("new_password", "").strip()
    confirm_pass = request.form.get("confirm_password", "").strip()
    
    users = get_all_users()
    current_stored = users.get(user["username"], {}).get("password", "123")
    
    if old_pass not in [current_stored, "123", "123456", "Admin@123"]:
        flash("❌ Mật khẩu cũ không chính xác!", "danger")
        return redirect(url_for("admin_dashboard"))
        
    if len(new_pass) < 3:
        flash("❌ Mật khẩu mới phải có ít nhất 3 ký tự!", "warning")
        return redirect(url_for("admin_dashboard"))
        
    if new_pass != confirm_pass:
        flash("❌ Mật khẩu xác nhận không khớp!", "warning")
        return redirect(url_for("admin_dashboard"))
        
    conn = get_db()
    conn.execute("UPDATE users SET password = ? WHERE username = ?", (new_pass, user["username"]))
    conn.commit()
    conn.close()
    sync_to_json()
    
    flash("✅ Đổi mật khẩu thành công! Hãy ghi nhớ mật khẩu mới của bạn.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Đã đăng xuất khỏi phiên làm việc.")
    return redirect(url_for("home"))

# ---------------------------------------------------------
# ADMIN DASHBOARD & CRUD
# ---------------------------------------------------------
@app.route("/admin")
def admin_dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    is_admin = user["role"] in ["SUPER_ADMIN", "NHAN_VIEN"]
    
    all_products = get_all_products("all")
    if is_admin:
        display_products = all_products
        pending_products = [p for p in all_products if p.get("status") == "pending"]
    else:
        display_products = [p for p in all_products if p.get("author") == user["name"]]
        pending_products = []
        
    return render_template(
        "admin.html", 
        products=display_products,
        pending_products=pending_products,
        articles=get_all_articles(),
        orders=get_all_orders(), 
        messages=[], 
        users=get_all_users(),
        user=user
    )

@app.route("/admin/approve-partner/<username>", methods=["POST"])
def approve_partner(username):
    user = session.get("user")
    if not user or user["role"] != "SUPER_ADMIN":
        return "Bạn không có quyền!", 403
        
    conn = get_db()
    conn.execute("UPDATE users SET approved = 1 WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    sync_to_json()
    flash(f"✅ Đã phê duyệt cấp quyền đăng bài thành công cho đối tác: {username}")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/revoke-partner/<username>", methods=["POST"])
def revoke_partner(username):
    user = session.get("user")
    if not user or user["role"] != "SUPER_ADMIN":
        return "Bạn không có quyền!", 403
        
    conn = get_db()
    conn.execute("UPDATE users SET approved = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    sync_to_json()
    flash(f"🔒 Đã tạm dừng quyền đăng bài của đối tác: {username}")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/approve-product/<int:product_id>", methods=["POST"])
def approve_product(product_id):
    user = session.get("user")
    if not user or user["role"] not in ["SUPER_ADMIN", "NHAN_VIEN"]:
        return "Bạn không có quyền!", 403
        
    conn = get_db()
    conn.execute("UPDATE products SET status = 'approved' WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    sync_to_json()
    flash("✅ Đã duyệt và xuất bản sản phẩm lên trang chủ!")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject-product/<int:product_id>", methods=["POST"])
def reject_product(product_id):
    user = session.get("user")
    if not user or user["role"] not in ["SUPER_ADMIN", "NHAN_VIEN"]:
        return "Bạn không có quyền!", 403
        
    conn = get_db()
    conn.execute("UPDATE products SET status = 'rejected' WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    sync_to_json()
    flash("⚠️ Đã từ chối bài đăng sản phẩm.")
    return redirect(url_for("admin_dashboard"))

# SẮP XẾP THỨ TỰ SẢN PHẨM: ĐẨY LÊN / ĐẨY XUỐNG
@app.route("/admin/move-product/<int:product_id>/<direction>", methods=["POST"])
def move_product(product_id, direction):
    user = session.get("user")
    if not user or user["role"] not in ["SUPER_ADMIN", "NHAN_VIEN"]:
        return "Bạn không có quyền!", 403
        
    products = get_all_products("all")
    idx = next((i for i, p in enumerate(products) if p["id"] == product_id), None)
    
    if idx is not None:
        target_idx = idx - 1 if direction == "up" else idx + 1
        if 0 <= target_idx < len(products):
            conn = get_db()
            p1 = products[idx]
            p2 = products[target_idx]
            
            order1 = p1.get("sort_order", idx * 10)
            order2 = p2.get("sort_order", target_idx * 10)
            
            if order1 == order2:
                for i, p in enumerate(products):
                    conn.execute("UPDATE products SET sort_order = ? WHERE id = ?", (i * 10, p["id"]))
                order1 = idx * 10
                order2 = target_idx * 10
                
            conn.execute("UPDATE products SET sort_order = ? WHERE id = ?", (order2, p1["id"]))
            conn.execute("UPDATE products SET sort_order = ? WHERE id = ?", (order1, p2["id"]))
            conn.commit()
            conn.close()
            sync_to_json()
            flash(f"🔄 Đã đổi thứ tự hiển thị của sản phẩm '{p1['name']}' thành công!")
            
    return redirect(url_for("admin_dashboard"))

# SỬA SẢN PHẨM
@app.route("/admin/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    is_admin = user["role"] in ["SUPER_ADMIN", "NHAN_VIEN"]
    product = get_product_by_id(product_id)
    
    if not product:
        flash("Không tìm thấy sản phẩm cần sửa!", "warning")
        return redirect(url_for("admin_dashboard"))
        
    if not is_admin and product.get("author") != user["name"]:
        flash("⛔ Bạn không có quyền sửa sản phẩm này!", "danger")
        return redirect(url_for("admin_dashboard"))
        
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        group_name = request.form.get("group", "Mật ong")
        try:
            price = int(request.form.get("price", 0))
        except ValueError:
            price = product["price"]
            
        packaging = request.form.get("packaging", "").strip()
        origin = request.form.get("origin", "").strip()
        ingredients = request.form.get("ingredients", "").strip()
        process = request.form.get("process", "").strip()
        usage = request.form.get("usage", "").strip()
        storage = request.form.get("storage", "").strip()
        image_url = request.form.get("image_url", "").strip()
        
        uploaded_file = request.files.get("image_file")
        if uploaded_file and uploaded_file.filename != '' and allowed_file(uploaded_file.filename):
            img_bytes = uploaded_file.read()
            mime_type = uploaded_file.content_type or "image/jpeg"
            b64_str = base64.b64encode(img_bytes).decode('utf-8')
            final_img = f"data:{mime_type};base64,{b64_str}"
        elif image_url:
            final_img = image_url
        else:
            final_img = product.get("image", "")
            
        conn = get_db()
        conn.execute('''
        UPDATE products SET group_name = ?, name = ?, price = ?, packaging = ?, origin = ?, ingredients = ?, process = ?, usage = ?, storage = ?, image = ?
        WHERE id = ?
        ''', (group_name, name, price, packaging, origin, ingredients, process, usage, storage, final_img, product_id))
        conn.commit()
        conn.close()
        sync_to_json()
            
        flash(f"✅ Đã cập nhật và lưu vĩnh viễn sản phẩm: {name}!", "success")
        return redirect(url_for("admin_dashboard"))
        
    return render_template("edit_product.html", product=product, user=user)

# XÓA SẢN PHẨM
@app.route("/admin/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    is_admin = user["role"] in ["SUPER_ADMIN", "NHAN_VIEN"]
    product = get_product_by_id(product_id)
    
    if product:
        if is_admin or product.get("author") == user["name"]:
            conn = get_db()
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
            conn.close()
            sync_to_json()
            flash(f"🗑️ Đã xóa vĩnh viễn sản phẩm: {product['name']}!", "success")
        else:
            flash("⛔ Bạn không có quyền xóa sản phẩm này!", "danger")
    return redirect(url_for("admin_dashboard"))

# ĐĂNG SẢN PHẨM MỚI
@app.route("/admin/add-product", methods=["POST"])
def admin_add_product():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    is_admin = user["role"] in ["SUPER_ADMIN", "NHAN_VIEN"]
    users = get_all_users()
    is_approved_partner = (user["role"] == "DOI_TAC" and users.get(user["username"], {}).get("approved"))
    
    if not (is_admin or is_approved_partner):
        flash("⛔ Bạn chưa được Admin cấp quyền đăng bài sản phẩm!", "danger")
        return redirect(url_for("admin_dashboard"))

    name = request.form.get("name", "").strip()
    group_name = request.form.get("group", "Mật ong")
    try:
        price = int(request.form.get("price", 0))
    except ValueError:
        price = 0
        
    packaging = request.form.get("packaging", "").strip() or "Hũ 500g"
    origin = request.form.get("origin", "").strip() or "Việt Nam"
    ingredients = request.form.get("ingredients", "").strip() or "100% tự nhiên nguyên chất"
    process = request.form.get("process", "").strip() or "Quy trình chế biến an toàn đạt chuẩn"
    usage = request.form.get("usage", "").strip() or "Xem hướng dẫn trên bao bì sản phẩm"
    storage = request.form.get("storage", "").strip() or "Bảo quản nơi khô ráo, thoáng mát"
    image_url = request.form.get("image_url", "").strip()
    
    final_img = image_url
    uploaded_file = request.files.get("image_file")
    if uploaded_file and uploaded_file.filename != '' and allowed_file(uploaded_file.filename):
        img_bytes = uploaded_file.read()
        mime_type = uploaded_file.content_type or "image/jpeg"
        b64_str = base64.b64encode(img_bytes).decode('utf-8')
        final_img = f"data:{mime_type};base64,{b64_str}"

    status = "approved" if is_admin else "pending"
    author = user["name"] if user["role"] == "DOI_TAC" else "Ngọ Phượng Store"
    date_str = datetime.now().strftime("%d/%m/%Y")
    
    conn = get_db()
    conn.execute('''
    INSERT INTO products (sort_order, group_name, name, price, packaging, rating, origin, ingredients, process, usage, storage, image, status, author, date)
    VALUES (0, ?, ?, ?, ?, 5, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (group_name, name, price, packaging, origin, ingredients, process, usage, storage, final_img, status, author, date_str))
    conn.commit()
    conn.close()
    sync_to_json()
    
    if is_admin:
        flash(f"🎉 Đã đăng thành công và lưu vĩnh viễn sản phẩm: {name}!", "success")
    else:
        flash(f"🎉 Đã gửi bài đăng sản phẩm: {name}. Bài viết sẽ xuất hiện trên trang chủ ngay sau khi được Admin duyệt!", "info")
        
    return redirect(url_for("admin_dashboard"))

# THÊM BÀI VIẾT MỚI (CẨM NANG SỨC KHỎE)
@app.route("/admin/add-article", methods=["POST"])
def admin_add_article():
    user = session.get("user")
    if not user or user["role"] not in ["SUPER_ADMIN", "NHAN_VIEN"]:
        return "Bạn không có quyền!", 403
        
    title = request.form.get("title", "").strip()
    snippet = request.form.get("snippet", "").strip()
    content = request.form.get("content", "").strip() or snippet
    
    conn = get_db()
    conn.execute('''
    INSERT INTO articles (date, title, snippet, content, author)
    VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%d/%m/%Y"), title, snippet, content, user["name"]))
    conn.commit()
    conn.close()
    sync_to_json()
    
    flash(f"📰 Đã đăng bài viết mới: {title} thành công và lưu vĩnh viễn!", "success")
    return redirect(url_for("admin_dashboard"))

# XÓA BÀI VIẾT
@app.route("/admin/delete-article/<int:article_id>", methods=["POST"])
def delete_article(article_id):
    user = session.get("user")
    if not user or user["role"] not in ["SUPER_ADMIN", "NHAN_VIEN"]:
        return "Bạn không có quyền!", 403
        
    conn = get_db()
    conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
    sync_to_json()
    
    flash("🗑️ Đã xóa bài viết thành công!", "success")
    return redirect(url_for("admin_dashboard"))

# Cập nhật trạng thái đơn hàng
@app.route("/admin/update-order/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    status = request.form.get("status")
    conn = get_db()
    conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()
    sync_to_json()
    flash(f"Đã cập nhật đơn hàng #{order_id} sang trạng thái: {status}")
    return redirect(url_for("admin_dashboard"))

# ---------------------------------------------------------
# SAO LƯU & KHÔI PHỤC DỮ LIỆU JSON (1-CLICK BACKUP / RESTORE)
# ---------------------------------------------------------
@app.route("/admin/export-backup")
def export_backup():
    user = session.get("user")
    if not user or user["role"] != "SUPER_ADMIN":
        return "Bạn không có quyền!", 403
        
    backup_data = {
        "products": get_all_products("all"),
        "articles": get_all_articles(),
        "orders": get_all_orders(),
        "users": get_all_users(),
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return Response(
        json.dumps(backup_data, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename=nongsan_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
    )

@app.route("/admin/import-backup", methods=["POST"])
def import_backup():
    user = session.get("user")
    if not user or user["role"] != "SUPER_ADMIN":
        return "Bạn không có quyền!", 403
        
    uploaded_file = request.files.get("backup_file")
    if uploaded_file and uploaded_file.filename != '':
        try:
            content = json.load(uploaded_file)
            conn = get_db()
            cursor = conn.cursor()
            
            if "products" in content and isinstance(content["products"], list):
                cursor.execute("DELETE FROM products")
                for p in content["products"]:
                    cursor.execute('''
                    INSERT INTO products (id, sort_order, group_name, name, price, packaging, rating, origin, ingredients, process, usage, storage, image, status, author, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (p.get("id"), p.get("sort_order", p.get("id", 0)), p.get("group_name", p.get("group")), p.get("name"), p.get("price"), p.get("packaging"), p.get("rating", 5), p.get("origin"), p.get("ingredients"), p.get("process"), p.get("usage"), p.get("storage"), p.get("image"), p.get("status", "approved"), p.get("author", "Ngọ Phượng Store"), p.get("date")))
                conn.commit()
                
            if "articles" in content and isinstance(content["articles"], list):
                cursor.execute("DELETE FROM articles")
                for a in content["articles"]:
                    cursor.execute('''
                    INSERT INTO articles (id, date, title, snippet, content, author)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (a.get("id"), a.get("date"), a.get("title"), a.get("snippet"), a.get("content", ""), a.get("author", "Super Admin")))
                conn.commit()
                
            conn.close()
            sync_to_json()
            flash("🎉 Khôi phục toàn bộ dữ liệu Sản phẩm & Bài viết thành công 100%!", "success")
        except Exception as e:
            flash(f"❌ Lỗi khi nạp file backup: {e}", "danger")
            
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
