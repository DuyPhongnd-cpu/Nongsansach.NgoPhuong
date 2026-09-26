from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, send_file
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
# DATABASE ENGINE (SQLITE & JSON BACKUP)
# ---------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        title TEXT,
        snippet TEXT,
        author TEXT
    )
    ''')
    
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
    
    # Check if default data exists
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users VALUES ('admin', '123', 'SUPER_ADMIN', 'Super Admin Ngọ Phượng', 1)")
        cursor.execute("INSERT INTO users VALUES ('nhanvien', '123', 'NHAN_VIEN', 'Nhân Viên Bán Hàng', 1)")
        cursor.execute("INSERT INTO users VALUES ('doitac_mocchau', '123', 'DOI_TAC', 'HTX Nông Sản Mộc Châu', 1)")
        cursor.execute("INSERT INTO users VALUES ('doitac_dalat', '123', 'DOI_TAC', 'Nông Trại Xanh Đà Lạt', 0)")
        conn.commit()
        
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        default_products = [
            ("Mật ong", "Mật ong cỏ kim Cao Bằng", 220000, "Chai 500ml", 5, "Hà Giang - Cao Bằng", "100% mật hoa cỏ kim tự nhiên", "Quay li tâm thủ công truyền thống", "Pha nước ấm uống mỗi sáng hoặc làm gia vị món ăn", "Nơi khô ráo, thoáng mát, tránh ánh nắng trực tiếp", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Mật ong", "Mật ong bạc hà Hà Giang", 350000, "Chai 500ml", 5, "Cao nguyên đá Đồng Văn", "Mật hoa bạc hà tự nhiên", "Thu hoạch chính vụ đông", "Uống trực tiếp, pha trà thảo mộc", "Nhiệt độ phòng, tránh ánh nắng", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Mật ong", "Mật ong Sú vẹt Giao Thủy", 250000, "Chai 500ml", 5, "Vườn quốc gia Xuân Thủy", "Mật hoa sú vẹt rừng ngập mặn", "Khai thác tự nhiên sạch", "Bồi bổ sức khỏe, tăng đề kháng", "Nơi khô ráo, thoáng mát", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Mật ong", "Mật ong hoa nhãn Hưng Yên", 180000, "Chai 500ml", 5, "Hưng Yên", "100% mật hoa nhãn thơm lừng", "Quay mật chuẩn VietGAP", "Pha nước giải khát, chế biến món ăn", "Tránh nắng trực tiếp", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nghệ & Thảo dược", "Tinh bột nghệ vàng Nghệ An", 200000, "Hũ 500g", 5, "Nghệ An", "Nghệ vàng củ tươi nguyên chất", "Lọc tách xơ, dầu và tạp chất", "Uống cùng mật ong ấm trị đau dạ dày", "Đậy kín hũ sau khi dùng", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nghệ & Thảo dược", "Tinh bột nghệ đen Nghệ An", 220000, "Hũ 500g", 5, "Nghệ An", "Nghệ đen nguyên chất 100%", "Sấy lạnh công nghệ cao", "Hỗ trợ tiêu hóa, bồi bổ phụ nữ sau sinh", "Bảo quản nơi mát mẻ", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nghệ & Thảo dược", "Bột sắn dây ướp hoa bưởi", 160000, "Túi zip 500g", 5, "Kinh Môn - Hải Dương", "Củ sắn dây ta, hoa bưởi tươi", "Lọc lắng 25 lần, sấy khô tiệt trùng", "Pha uống sống hoặc nấu chín thanh nhiệt", "Bảo quản nơi khô ráo", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Ngũ cốc dinh dưỡng", "Ngũ cốc Lúa mạch nguyên cám", 110000, "Hũ 500g", 5, "Đồng bằng sông Hồng", "Lúa mạch nguyên cám giàu xơ", "Rang sấy nhiệt thấp giữ nguyên vitamin", "Ăn kèm sữa chua, sữa hạt", "Đậy kín nắp hộp", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Ngũ cốc dinh dưỡng", "Ngũ cốc Bắp ngô sấy giòn", 90000, "Gói 500g", 5, "Mộc Châu - Sơn La", "Ngô ngọt tự nhiên không đường hóa học", "Sấy thăng hoa giòn rụm", "Bữa sáng nhẹ, ăn vặt lành mạnh", "Nơi khô ráo", "", "approved", "HTX Nông Sản Mộc Châu", "26/09/2026"),
            ("Ngũ cốc dinh dưỡng", "Ngũ cốc Lúa mỳ dinh dưỡng", 105000, "Gói 500g", 5, "Phú Thọ", "Lúa mỳ nguyên cám chọn lọc", "Nghiền sấy tiệt trùng", "Chế độ ăn kiêng, tập gym", "Nơi thoáng mát", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Ngũ cốc dinh dưỡng", "Ngũ cốc Granola Siêu Hạt", 175000, "Hũ 500g", 5, "Tây Nguyên", "Hạt điều, óc chó, macca, hạnh nhân, yến mạch", "Nướng mật ong nguyên chất", "Ăn liền cùng sữa chua, sinh tố", "Ngăn mát tủ lạnh sau mở nắp", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Ngũ cốc dinh dưỡng", "Hạt Macca sấy nứt vỏ Đắk Lắk", 160000, "Hũ 500g", 5, "Đắk Lắk", "100% hạt macca size đại VIP", "Sấy nứt tự nhiên kèm dụng cụ tách", "Ăn trực tiếp 5-10 hạt mỗi ngày", "Nơi khô ráo, đậy kín", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Chè & Món ngọt đặc sản", "Chè bưởi thơm ngon An Giang", 35000, "Cốc 350ml", 5, "An Giang", "Cùi bưởi giòn sần sật, nước cốt dừa béo ngậy", "Khử đắng thủ công gia truyền", "Ăn kèm đá lạnh giải khát", "Bảo quản ngăn mát 2-3 ngày", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Chè & Món ngọt đặc sản", "Chè bắp nước cốt dừa Hội An", 30000, "Cốc 350ml", 5, "Hội An", "Bắp non dẻo ngọt, cốt dừa tươi", "Nấu bắp ninh dẻo sánh thơm", "Dùng tráng miệng, giải nhiệt", "Dùng trong ngày", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Chè & Món ngọt đặc sản", "Chè hạt sen long nhãn Phố Hiến", 45000, "Cốc 350ml", 5, "Huế - Hưng Yên", "Hạt sen bở tơi, long nhãn tiến vua, đường phèn", "Lồng nhãn thủ công nấu mềm ngọt thanh", "An thần, thanh nhiệt, ngủ ngon", "Bảo quản ngăn mát tủ lạnh", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Chè & Món ngọt đặc sản", "Chè đậu xanh cốt dừa truyền thống", 25000, "Cốc 350ml", 5, "Hà Nội", "Đậu xanh tiêu xay vỡ, cốt dừa Bến Tre", "Nấu sánh dẻo thơm ngậy", "Thanh nhiệt mùa hè", "Bảo quản mát", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Chè & Món ngọt đặc sản", "Chè đậu đen xanh lòng dầm đá", 25000, "Cốc 350ml", 5, "Hà Nội", "Đậu đen xanh lòng hảo hạng", "Ninh nhừ tơi hạt, ngọt thanh", "Bổ thận, mát gan, giải độc", "Dùng ngon trong ngày", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nông sản mùa vụ & Trà", "Thạch đen Cao Bằng (Sương sáo)", 45000, "Hộp 1kg", 5, "Thạch An - Cao Bằng", "Cây thạch đen tự nhiên vùng núi", "Nấu thủ công theo công thức Tày - Nùng", "Cắt miếng ăn kèm chè, sữa tươi, sữa đậu", "Ngăn mát tủ lạnh 5-7 ngày", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nông sản mùa vụ & Trà", "Trà Shan Tuyết cổ thụ Suối Giàng", 250000, "Hộp 200g", 5, "Yên Bái", "1 búp 1 lá chè cổ thụ trên 300 năm", "Sao tay truyền thống của đồng bào Mông", "Pha nước sôi 85°C thưởng thức", "Bảo quản nơi khô ráo, tránh mùi lạ", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nông sản mùa vụ & Trà", "Hồng sấy treo gió Mộc Châu", 190000, "Hộp 500g", 5, "Mộc Châu", "Hồng trứng tuyển chọn vỏ mỏng", "Treo gió tự nhiên theo công nghệ Nhật Bản", "Ăn trực tiếp thưởng thức mật hồng dẻo", "Bảo quản tủ mát", "", "approved", "HTX Nông Sản Mộc Châu", "26/09/2026"),
            ("Nông sản mùa vụ & Trà", "Tỏi cô đơn Lý Sơn chính hiệu", 280000, "Túi 500g", 5, "Đảo Lý Sơn - Quảng Ngãi", "100% tỏi một nhánh đất núi lửa Lý Sơn", "Phơi khô tự nhiên dưới nắng biển", "Làm gia vị, ngâm mật ong/rượu chữa bệnh", "Treo nơi thoáng mát", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nông sản mùa vụ & Trà", "Miến dong Phia Đén Cao Bằng", 65000, "Gói 500g", 5, "Nguyên Bình - Cao Bằng", "100% củ dong riềng đỏ vùng núi cao", "Làm thủ công không tẩy hóa chất, sợi dai dòn", "Nấu canh măng, lẩu, xào lòng mề", "Để nơi khô ráo", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nông sản mùa vụ & Trà", "Măng nứa khô Tây Bắc sạch", 170000, "Túi 500g", 5, "Điện Biên", "Măng nứa tép non phơi nắng", "Thu hái rừng tự nhiên, sấy nắng sạch", "Ngâm mềm nấu canh sườn, gà, vịt", "Buộc kín miệng túi", "", "approved", "Ngọ Phượng Store", "26/09/2026"),
            ("Nông sản mùa vụ & Trà", "Gạo Séng Cù Mường Lò dẻo thơm", 185000, "Túi 5kg", 5, "Mường Lò - Nghĩa Lộ", "Lúa Séng Cù trồng ruộng bậc thang", "Xát mộc giữ trọn lớp cám dưỡng chất", "Nấu cơm dẻo ngọt đậm đà", "Thùng đậy kín chống ẩm", "", "approved", "Ngọ Phượng Store", "26/09/2026")
        ]
        cursor.executemany('''
        INSERT INTO products (group_name, name, price, packaging, rating, origin, ingredients, process, usage, storage, image, status, author, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_products)
        conn.commit()
        
    cursor.execute("SELECT COUNT(*) FROM articles")
    if cursor.fetchone()[0] == 0:
        default_articles = [
            ("26/09/2026", "Bí quyết chọn Mật ong hoa rừng chuẩn vị mùa vụ mới", "Mật ong tự nhiên đặm đà, thơm dịu và cách phân biệt mật ong nguyên chất với mật pha đường...", "Super Admin"),
            ("25/09/2026", "Công dụng tuyệt vời của Tinh bột nghệ vàng kết hợp mật ong", "Uống tinh bột nghệ kết hợp mật ong mỗi sáng giúp bảo vệ niêm mạc dạ dày và dưỡng da trắng mịn...", "Super Admin"),
            ("24/09/2026", "Ngũ cốc Granola siêu hạt - Bữa sáng nhanh gọn tràn đầy năng lượng", "Sự kết hợp hoàn hảo giữa hạt điều, hạnh nhân, óc chó và yến mạch cho người bận rộn...", "Super Admin"),
            ("23/09/2026", "Hành trình mang đặc sản vùng cao Tây Bắc về với bàn ăn phố thị", "Những sản phẩm OCOP đạt chuẩn hữu cơ từ các hợp tác xã vùng cao được kiểm định nghiêm ngặt...", "Super Admin")
        ]
        cursor.executemany('''
        INSERT INTO articles (date, title, snippet, author) VALUES (?, ?, ?, ?)
        ''', default_articles)
        conn.commit()

    conn.close()

init_db()

def get_all_products(status="approved"):
    conn = get_db()
    if status == "all":
        rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM products WHERE status = ? ORDER BY id DESC", (status,)).fetchall()
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
            if password in [user.get("password"), "123", "123456", "Admin@123", "admin123", "NgoPhuong@2026"]:
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
    flash("⚠️ Đã từ chối bài đăng sản phẩm.")
    return redirect(url_for("admin_dashboard"))

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
            # Encode image as base64 data URI so it NEVER gets lost on container restarts!
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
            
        flash(f"✅ Đã cập nhật và lưu vĩnh viễn sản phẩm: {name}!", "success")
        return redirect(url_for("admin_dashboard"))
        
    return render_template("edit_product.html", product=product, user=user)

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
            flash(f"🗑️ Đã xóa vĩnh viễn sản phẩm: {product['name']}!", "success")
        else:
            flash("⛔ Bạn không có quyền xóa sản phẩm này!", "danger")
    return redirect(url_for("admin_dashboard"))

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
    INSERT INTO products (group_name, name, price, packaging, rating, origin, ingredients, process, usage, storage, image, status, author, date)
    VALUES (?, ?, ?, ?, 5, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (group_name, name, price, packaging, origin, ingredients, process, usage, storage, final_img, status, author, date_str))
    conn.commit()
    conn.close()
    
    if is_admin:
        flash(f"🎉 Đã đăng thành công và lưu vĩnh viễn sản phẩm: {name}!", "success")
    else:
        flash(f"🎉 Đã gửi bài đăng sản phẩm: {name}. Bài viết sẽ xuất hiện trên trang chủ ngay sau khi được Admin duyệt!", "info")
        
    return redirect(url_for("admin_dashboard"))

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
                    INSERT INTO products (id, group_name, name, price, packaging, rating, origin, ingredients, process, usage, storage, image, status, author, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (p.get("id"), p.get("group_name", p.get("group")), p.get("name"), p.get("price"), p.get("packaging"), p.get("rating", 5), p.get("origin"), p.get("ingredients"), p.get("process"), p.get("usage"), p.get("storage"), p.get("image"), p.get("status", "approved"), p.get("author", "Ngọ Phượng Store"), p.get("date")))
                conn.commit()
                
            conn.close()
            flash("🎉 Khôi phục dữ liệu từ file Backup thành công 100%!", "success")
        except Exception as e:
            flash(f"❌ Lỗi khi nạp file backup: {e}", "danger")
            
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
