from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nongsan_ngophuong_secret_key_2026")

USERS = {
    "admin": {"password": "123", "role": "SUPER_ADMIN", "name": "Super Admin Ngọ Phượng", "approved": True},
    "nhanvien": {"password": "123", "role": "NHAN_VIEN", "name": "Nhân Viên Bán Hàng", "approved": True},
    "doitac_mocchau": {"password": "123", "role": "DOI_TAC", "name": "HTX Nông Sản Mộc Châu", "approved": True},
    "doitac_dalat": {"password": "123", "role": "DOI_TAC", "name": "Nông Trại Xanh Đà Lạt", "approved": False}
}

PRODUCTS = [
    {"id": 1, "group": "Mật ong", "name": "Mật ong cỏ kim Cao Bằng", "price": 220000, "packaging": "Chai 500ml", "rating": 5, "origin": "Hà Giang - Cao Bằng", "ingredients": "100% mật hoa cỏ kim tự nhiên", "process": "Quay li tâm thủ công", "usage": "Pha nước ấm uống mỗi sáng", "storage": "Nơi khô ráo, thoáng mát"},
    {"id": 2, "group": "Mật ong", "name": "Mật ong bạc hà Hà Giang", "price": 350000, "packaging": "Chai 500ml", "rating": 5, "origin": "Cao nguyên đá Đồng Văn", "ingredients": "Mật hoa bạc hà tự nhiên", "process": "Thu hoạch chính vụ đông", "usage": "Uống trực tiếp, pha trà thảo mộc", "storage": "Nhiệt độ phòng, tránh ánh nắng"},
    {"id": 3, "group": "Mật ong", "name": "Mật ong Sú vẹt Giao Thủy", "price": 250000, "packaging": "Chai 500ml", "rating": 5, "origin": "Vườn quốc gia Xuân Thủy", "ingredients": "Mật hoa sú vẹt rừng ngập mặn", "process": "Khai thác tự nhiên sạch", "usage": "Bồi bổ sức khỏe, tăng đề kháng", "storage": "Nơi khô ráo, thoáng mát"},
    {"id": 4, "group": "Mật ong", "name": "Mật ong hoa nhãn Hưng Yên", "price": 180000, "packaging": "Chai 500ml", "rating": 5, "origin": "Hưng Yên", "ingredients": "100% mật hoa nhãn thơm lừng", "process": "Quay mật chuẩn VietGAP", "usage": "Pha nước giải khát, chế biến món ăn", "storage": "Tránh nắng trực tiếp"},
    {"id": 5, "group": "Nghệ & Thảo dược", "name": "Tinh bột nghệ vàng Nghệ An", "price": 200000, "packaging": "Hũ 500g", "rating": 5, "origin": "Nghệ An", "ingredients": "Nghệ vàng củ tươi nguyên chất", "process": "Lọc tách xơ, dầu và tạp chất", "usage": "Uống cùng mật ong ấm trị đau dạ dày", "storage": "Đậy kín hũ sau khi dùng"},
    {"id": 6, "group": "Nghệ & Thảo dược", "name": "Tinh bột nghệ đen Nghệ An", "price": 220000, "packaging": "Hũ 500g", "rating": 5, "origin": "Nghệ An", "ingredients": "Nghệ đen nguyên chất 100%", "process": "Sấy lạnh công nghệ cao", "usage": "Hỗ trợ tiêu hóa, bồi bổ phụ nữ sau sinh", "storage": "Bảo quản nơi mát mẻ"},
    {"id": 7, "group": "Nghệ & Thảo dược", "name": "Bột sắn dây ướp hoa bưởi", "price": 160000, "packaging": "Túi zip 500g", "rating": 5, "origin": "Kinh Môn - Hải Dương", "ingredients": "Củ sắn dây ta, hoa bưởi tươi", "process": "Lọc lắng 25 lần, sấy khô tiệt trùng", "usage": "Pha uống sống hoặc nấu chín thanh nhiệt", "storage": "Bảo quản nơi khô ráo"},
    {"id": 8, "group": "Ngũ cốc dinh dưỡng", "name": "Ngũ cốc Lúa mạch nguyên cám", "price": 110000, "packaging": "Hũ 500g", "rating": 5, "origin": "Đồng bằng sông Hồng", "ingredients": "Lúa mạch nguyên cám giàu xơ", "process": "Rang sấy nhiệt thấp giữ nguyên vitamin", "usage": "Ăn kèm sữa chua, sữa hạt", "storage": "Đậy kín nắp hộp"},
    {"id": 9, "group": "Ngũ cốc dinh dưỡng", "name": "Ngũ cốc Bắp ngô sấy giòn", "price": 90000, "packaging": "Gói 500g", "rating": 5, "origin": "Mộc Châu - Sơn La", "ingredients": "Ngô ngọt tự nhiên không đường hóa học", "process": "Sấy thăng hoa giòn rụm", "usage": "Bữa sáng nhẹ, ăn vặt lành mạnh", "storage": "Nơi khô ráo"},
    {"id": 10, "group": "Ngũ cốc dinh dưỡng", "name": "Ngũ cốc Lúa mỳ dinh dưỡng", "price": 105000, "packaging": "Gói 500g", "rating": 5, "origin": "Phú Thọ", "ingredients": "Lúa mỳ nguyên cám chọn lọc", "process": "Nghiền sấy tiệt trùng", "usage": "Chế độ ăn kiêng, tập gym", "storage": "Nơi thoáng mát"},
    {"id": 11, "group": "Ngũ cốc dinh dưỡng", "name": "Ngũ cốc Granola Siêu Hạt", "price": 175000, "packaging": "Hũ 500g", "rating": 5, "origin": "Tây Nguyên", "ingredients": "Hạt điều, óc chó, macca, hạnh nhân, yến mạch", "process": "Nướng mật ong nguyên chất", "usage": "Ăn liền cùng sữa chua, sinh tố", "storage": "Ngăn mát tủ lạnh sau mở nắp"},
    {"id": 12, "group": "Ngũ cốc dinh dưỡng", "name": "Hạt Macca sấy nứt vỏ Đắk Lắk", "price": 160000, "packaging": "Hũ 500g", "rating": 5, "origin": "Đắk Lắk", "ingredients": "100% hạt macca size đại VIP", "process": "Sấy nứt tự nhiên kèm dụng cụ tách", "usage": "Ăn trực tiếp 5-10 hạt mỗi ngày", "storage": "Nơi khô ráo, đậy kín"},
    {"id": 13, "group": "Chè & Món ngọt đặc sản", "name": "Chè bưởi thơm ngon An Giang", "price": 35000, "packaging": "Cốc 350ml", "rating": 5, "origin": "An Giang", "ingredients": "Cùi bưởi giòn sần sật, nước cốt dừa béo ngậy", "process": "Khử đắng thủ công gia truyền", "usage": "Ăn kèm đá lạnh giải khát", "storage": "Bảo quản ngăn mát 2-3 ngày"},
    {"id": 14, "group": "Chè & Món ngọt đặc sản", "name": "Chè bắp nước cốt dừa Hội An", "price": 30000, "packaging": "Cốc 350ml", "rating": 5, "origin": "Hội An", "ingredients": "Bắp non dẻo ngọt, cốt dừa tươi", "process": "Nấu bắp ninh dẻo sánh thơm", "usage": "Dùng tráng miệng, giải nhiệt", "storage": "Dùng trong ngày"},
    {"id": 15, "group": "Chè & Món ngọt đặc sản", "name": "Chè hạt sen long nhãn Phố Hiến", "price": 45000, "packaging": "Cốc 350ml", "rating": 5, "origin": "Huế - Hưng Yên", "ingredients": "Hạt sen bở tơi, long nhãn tiến vua, đường phèn", "process": "Lồng nhãn thủ công nấu mềm ngọt thanh", "usage": "An thần, thanh nhiệt, ngủ ngon", "storage": "Bảo quản ngăn mát tủ lạnh"},
    {"id": 16, "group": "Chè & Món ngọt đặc sản", "name": "Chè đậu xanh cốt dừa truyền thống", "price": 25000, "packaging": "Cốc 350ml", "rating": 5, "origin": "Hà Nội", "ingredients": "Đậu xanh tiêu xay vỡ, cốt dừa Bến Tre", "process": "Nấu sánh dẻo thơm ngậy", "usage": "Thanh nhiệt mùa hè", "storage": "Bảo quản mát"},
    {"id": 17, "group": "Chè & Món ngọt đặc sản", "name": "Chè đậu đen xanh lòng dầm đá", "price": 25000, "packaging": "Cốc 350ml", "rating": 5, "origin": "Hà Nội", "ingredients": "Đậu đen xanh lòng hảo hạng", "process": "Ninh nhừ tơi hạt, ngọt thanh", "usage": "Bổ thận, mát gan, giải độc", "storage": "Dùng ngon trong ngày"},
    {"id": 18, "group": "Nông sản mùa vụ & Trà", "name": "Thạch đen Cao Bằng (Sương sáo)", "price": 45000, "packaging": "Hộp 1kg", "rating": 5, "origin": "Thạch An - Cao Bằng", "ingredients": "Cây thạch đen tự nhiên vùng núi", "process": "Nấu thủ công theo công thức Tày - Nùng", "usage": "Cắt miếng ăn kèm chè, sữa tươi, sữa đậu", "storage": "Ngăn mát tủ lạnh 5-7 ngày"},
    {"id": 19, "group": "Nông sản mùa vụ & Trà", "name": "Trà Shan Tuyết cổ thụ Suối Giàng", "price": 250000, "packaging": "Hộp 200g", "rating": 5, "origin": "Yên Bái", "ingredients": "1 búp 1 lá chè cổ thụ trên 300 năm", "process": "Sao tay truyền thống của đồng bào Mông", "usage": "Pha nước sôi 85°C thưởng thức", "storage": "Bảo quản nơi khô ráo, tránh mùi lạ"},
    {"id": 20, "group": "Nông sản mùa vụ & Trà", "name": "Hồng sấy treo gió Mộc Châu", "price": 190000, "packaging": "Hộp 500g", "rating": 5, "origin": "Mộc Châu", "ingredients": "Hồng trứng tuyển chọn vỏ mỏng", "process": "Treo gió tự nhiên theo công nghệ Nhật Bản", "usage": "Ăn trực tiếp thưởng thức mật hồng dẻo", "storage": "Bảo quản tủ mát"},
    {"id": 21, "group": "Nông sản mùa vụ & Trà", "name": "Tỏi cô đơn Lý Sơn chính hiệu", "price": 280000, "packaging": "Túi 500g", "rating": 5, "origin": "Đảo Lý Sơn - Quảng Ngãi", "ingredients": "100% tỏi một nhánh đất núi lửa Lý Sơn", "process": "Phơi khô tự nhiên dưới nắng biển", "usage": "Làm gia vị, ngâm mật ong/rượu chữa bệnh", "storage": "Treo nơi thoáng mát"},
    {"id": 22, "group": "Nông sản mùa vụ & Trà", "name": "Miến dong Phia Đén Cao Bằng", "price": 65000, "packaging": "Gói 500g", "rating": 5, "origin": "Nguyên Bình - Cao Bằng", "ingredients": "100% củ dong riềng đỏ vùng núi cao", "process": "Làm thủ công không tẩy hóa chất, sợi dai dòn", "usage": "Nấu canh măng, lẩu, xào lòng mề", "storage": "Để nơi khô ráo"},
    {"id": 23, "group": "Nông sản mùa vụ & Trà", "name": "Măng nứa khô Tây Bắc sạch", "price": 170000, "packaging": "Túi 500g", "rating": 5, "origin": "Điện Biên", "ingredients": "Măng nứa tép non phơi nắng", "process": "Thu hái rừng tự nhiên, sấy nắng sạch", "usage": "Ngâm mềm nấu canh sườn, gà, vịt", "storage": "Buộc kín miệng túi"},
    {"id": 24, "group": "Nông sản mùa vụ & Trà", "name": "Gạo Séng Cù Mường Lò dẻo thơm", "price": 185000, "packaging": "Túi 5kg", "rating": 5, "origin": "Mường Lò - Nghĩa Lộ", "ingredients": "Lúa Séng Cù trồng ruộng bậc thang", "process": "Xát mộc giữ trọn lớp cám dưỡng chất", "usage": "Nấu cơm dẻo ngọt đậm đà", "storage": "Thùng đậy kín chống ẩm"}
]

ARTICLES = [
    {"date": "24/09/2026", "title": "Bí quyết chọn Mật ong hoa rừng chuẩn vị mùa vụ mới", "snippet": "Mật ong tự nhiên đặm đà, thơm dịu và cách phân biệt mật ong nguyên chất với mật pha đường..."},
    {"date": "23/09/2026", "title": "Công dụng tuyệt vời của Tinh bột nghệ vàng kết hợp mật ong", "snippet": "Uống tinh bột nghệ kết hợp mật ong mỗi sáng giúp bảo vệ niêm mạc dạ dày và dưỡng da trắng mịn..."},
    {"date": "22/09/2026", "title": "Ngũ cốc Granola siêu hạt - Bữa sáng nhanh gọn tràn đầy năng lượng", "snippet": "Sự kết hợp hoàn hảo giữa hạt điều, hạnh nhân, óc chó và yến mạch cho người bận rộn..."},
    {"date": "21/09/2026", "title": "Hành trình mang đặc sản vùng cao Tây Bắc về với bàn ăn phố thị", "snippet": "Những sản phẩm OCOP đạt chuẩn hữu cơ từ các hợp tác xã vùng cao được kiểm định nghiêm ngặt..."}
]

ORDERS = []
MESSAGES = []

@app.route("/")
def home():
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    selected_group = request.args.get("group")
    if selected_group and selected_group != "all":
        display_products = [p for p in PRODUCTS if p["group"] == selected_group]
    else:
        display_products = PRODUCTS
        
    groups = sorted(list(set(p["group"] for p in PRODUCTS)))
    return render_template("index.html", products=display_products, articles=ARTICLES, cart_count=cart_count, groups=groups, selected_group=selected_group)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return "Sản phẩm không tồn tại", 404
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    related = [p for p in PRODUCTS if p["group"] == product["group"] and p["id"] != product["id"]][:4]
    return render_template("detail.html", product=product, related=related, cart_count=cart_count)

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    qty = int(request.form.get("qty", 1))
    cart = session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    session["cart"] = cart
    flash(f"Đã thêm sản phẩm vào giỏ hàng thành công!")
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
        product = next((p for p in PRODUCTS if p["id"] == int(p_id)), None)
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
        product = next((p for p in PRODUCTS if p["id"] == int(p_id)), None)
        if product:
            subtotal = product["price"] * qty
            total += subtotal
            order_items.append({"id": product["id"], "name": product["name"], "qty": qty, "price": product["price"]})

    order = {
        "id": len(ORDERS) + 1,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "customer": name,
        "phone": phone,
        "address": address,
        "payment": payment,
        "note": note,
        "items": order_items,
        "total": total,
        "status": "Mới đặt"
    }
    ORDERS.append(order)
    session["cart"] = {}
    return render_template("order_success.html", order=order)

@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name")
    phone = request.form.get("phone")
    content = request.form.get("content")
    MESSAGES.append({
        "id": len(MESSAGES) + 1,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "name": name,
        "phone": phone,
        "content": content,
        "reply": "",
        "emails": "Bichphuong.ngo@gmail.com, duyphongnd@gmail.com",
        "zalo": "0912965979, 0983521268"
    })
    flash("Cảm ơn bạn! Thông tin liên hệ đã được gửi đến Ban Quản trị Nông Sản Ngọ Phượng.")
    return redirect(url_for("home"))

@app.route("/portal", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user = USERS.get(username)
        if user and user["password"] == password:
            if user["role"] == "DOI_TAC" and not user.get("approved", False):
                flash("⚠️ Tài khoản Đối tác của bạn đang CHỜ ADMIN PHÊ DUYỆT. Vui lòng liên hệ Admin để được kích hoạt quyền đăng sản phẩm!", "warning")
                return render_template("login.html")
                
            session["user"] = {
                "username": username,
                "role": user["role"],
                "name": user["name"],
                "approved": user.get("approved", False)
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
    
    if partner_user in USERS:
        flash("⚠️ Tên tài khoản đã tồn tại trên hệ thống!", "warning")
        return redirect(url_for("login"))
        
    USERS[partner_user] = {
        "password": partner_pass,
        "role": "DOI_TAC",
        "name": f"{partner_name} (SĐT: {partner_phone})",
        "approved": False
    }
    flash("🎉 Đăng ký tài khoản Đối tác thành công! Vui lòng chờ Admin phê duyệt để bắt đầu đăng sản phẩm.", "success")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Đã đăng xuất khỏi phiên làm việc.")
    return redirect(url_for("home"))

@app.route("/admin")
def admin_dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    return render_template(
        "admin.html", 
        products=PRODUCTS, 
        orders=ORDERS, 
        messages=MESSAGES, 
        users=USERS,
        user=user
    )

@app.route("/admin/approve-partner/<username>", methods=["POST"])
def approve_partner(username):
    user = session.get("user")
    if not user or user["role"] != "SUPER_ADMIN":
        return "Bạn không có quyền thực hiện chức năng này!", 403
        
    if username in USERS:
        USERS[username]["approved"] = True
        flash(f"✅ Đã phê duyệt cấp quyền đăng sản phẩm thành công cho đối tác: {USERS[username]['name']}")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/revoke-partner/<username>", methods=["POST"])
def revoke_partner(username):
    user = session.get("user")
    if not user or user["role"] != "SUPER_ADMIN":
        return "Bạn không có quyền thực hiện chức năng này!", 403
        
    if username in USERS:
        USERS[username]["approved"] = False
        flash(f"🔒 Đã tạm dừng quyền đăng bài của đối tác: {USERS[username]['name']}")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/add-product", methods=["POST"])
def admin_add_product():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    is_admin = user["role"] in ["SUPER_ADMIN", "NHAN_VIEN"]
    is_approved_partner = (user["role"] == "DOI_TAC" and USERS.get(user["username"], {}).get("approved", False))
    
    if not (is_admin or is_approved_partner):
        flash("⛔ Bạn chưa được Admin cấp quyền đăng bài sản phẩm!", "danger")
        return redirect(url_for("admin_dashboard"))

    name = request.form.get("name")
    group = request.form.get("group")
    price = int(request.form.get("price", 0))
    packaging = request.form.get("packaging")
    origin = request.form.get("origin", "Việt Nam")
    ingredients = request.form.get("ingredients", "Tự nhiên nguyên chất")
    process = request.form.get("process", "Chế biến đạt chuẩn")
    usage = request.form.get("usage", "Xem trên bao bì")
    storage = request.form.get("storage", "Nơi khô ráo")
    
    new_p = {
        "id": len(PRODUCTS) + 1,
        "group": group,
        "name": name,
        "price": price,
        "packaging": packaging,
        "rating": 5,
        "origin": origin,
        "ingredients": ingredients,
        "process": process,
        "usage": usage,
        "storage": storage,
        "partner": user["name"] if user["role"] == "DOI_TAC" else "Ngọ Phượng Store"
    }
    PRODUCTS.append(new_p)
    flash(f"🎉 Đã đăng thành công sản phẩm: {name}!")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/update-order/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    status = request.form.get("status")
    for order in ORDERS:
        if order["id"] == order_id:
            order["status"] = status
            flash(f"Đã cập nhật đơn hàng #{order_id} sang trạng thái: {status}")
            break
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
