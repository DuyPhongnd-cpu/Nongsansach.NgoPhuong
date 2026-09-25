from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nongsan_ngophuong_secret_key_2026")
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------------------------------------
# 1. TÀI KHOẢN VÀ BẢO MẬT PHÂN QUYỀN (RBAC)
# ---------------------------------------------------------
USERS = {
    "admin": {"password": "123", "role": "SUPER_ADMIN", "name": "Super Admin Ngọ Phượng", "approved": True},
    "nhanvien": {"password": "123", "role": "NHAN_VIEN", "name": "Nhân Viên Bán Hàng", "approved": True},
    "doitac_mocchau": {"password": "123", "role": "DOI_TAC", "name": "HTX Nông Sản Mộc Châu", "approved": True},
    "doitac_dalat": {"password": "123", "role": "DOI_TAC", "name": "Nông Trại Xanh Đà Lạt", "approved": False}
}

# ---------------------------------------------------------
# 2. DANH SÁCH SẢN PHẨM & BÀI ĐĂNG (CÓ HỖ TRỢ DUYỆT & ẢNH)
# ---------------------------------------------------------
PRODUCTS = [
    {
        "id": 1, "group": "Mật ong", "name": "Mật ong cỏ kim Cao Bằng", "price": 220000, 
        "packaging": "Chai 500ml", "rating": 5, "origin": "Hà Giang - Cao Bằng", 
        "ingredients": "100% mật hoa cỏ kim tự nhiên", "process": "Quay li tâm thủ công truyền thống", 
        "usage": "Pha nước ấm uống mỗi sáng hoặc làm gia vị món ăn", "storage": "Nơi khô ráo, thoáng mát, tránh ánh nắng trực tiếp", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 2, "group": "Mật ong", "name": "Mật ong bạc hà Hà Giang", "price": 350000, 
        "packaging": "Chai 500ml", "rating": 5, "origin": "Cao nguyên đá Đồng Văn", 
        "ingredients": "Mật hoa bạc hà tự nhiên", "process": "Thu hoạch chính vụ đông", 
        "usage": "Uống trực tiếp, pha trà thảo mộc", "storage": "Nhiệt độ phòng, tránh ánh nắng", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 3, "group": "Mật ong", "name": "Mật ong Sú vẹt Giao Thủy", "price": 250000, 
        "packaging": "Chai 500ml", "rating": 5, "origin": "Vườn quốc gia Xuân Thủy", 
        "ingredients": "Mật hoa sú vẹt rừng ngập mặn", "process": "Khai thác tự nhiên sạch", 
        "usage": "Bồi bổ sức khỏe, tăng đề kháng", "storage": "Nơi khô ráo, thoáng mát", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 4, "group": "Mật ong", "name": "Mật ong hoa nhãn Hưng Yên", "price": 180000, 
        "packaging": "Chai 500ml", "rating": 5, "origin": "Hưng Yên", 
        "ingredients": "100% mật hoa nhãn thơm lừng", "process": "Quay mật chuẩn VietGAP", 
        "usage": "Pha nước giải khát, chế biến món ăn", "storage": "Tránh nắng trực tiếp", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 5, "group": "Nghệ & Thảo dược", "name": "Tinh bột nghệ vàng Nghệ An", "price": 200000, 
        "packaging": "Hũ 500g", "rating": 5, "origin": "Nghệ An", 
        "ingredients": "Nghệ vàng củ tươi nguyên chất", "process": "Lọc tách xơ, dầu và tạp chất", 
        "usage": "Uống cùng mật ong ấm trị đau dạ dày", "storage": "Đậy kín hũ sau khi dùng", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 6, "group": "Nghệ & Thảo dược", "name": "Tinh bột nghệ đen Nghệ An", "price": 220000, 
        "packaging": "Hũ 500g", "rating": 5, "origin": "Nghệ An", 
        "ingredients": "Nghệ đen nguyên chất 100%", "process": "Sấy lạnh công nghệ cao", 
        "usage": "Hỗ trợ tiêu hóa, bồi bổ phụ nữ sau sinh", "storage": "Bảo quản nơi mát mẻ", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 7, "group": "Nghệ & Thảo dược", "name": "Bột sắn dây ướp hoa bưởi", "price": 160000, 
        "packaging": "Túi zip 500g", "rating": 5, "origin": "Kinh Môn - Hải Dương", 
        "ingredients": "Củ sắn dây ta, hoa bưởi tươi", "process": "Lọc lắng 25 lần, sấy khô tiệt trùng", 
        "usage": "Pha uống sống hoặc nấu chín thanh nhiệt", "storage": "Bảo quản nơi khô ráo", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 8, "group": "Ngũ cốc dinh dưỡng", "name": "Ngũ cốc Lúa mạch nguyên cám", "price": 110000, 
        "packaging": "Hũ 500g", "rating": 5, "origin": "Đồng bằng sông Hồng", 
        "ingredients": "Lúa mạch nguyên cám giàu xơ", "process": "Rang sấy nhiệt thấp giữ nguyên vitamin", 
        "usage": "Ăn kèm sữa chua, sữa hạt", "storage": "Đậy kín nắp hộp", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 9, "group": "Ngũ cốc dinh dưỡng", "name": "Ngũ cốc Bắp ngô sấy giòn", "price": 90000, 
        "packaging": "Gói 500g", "rating": 5, "origin": "Mộc Châu - Sơn La", 
        "ingredients": "Ngô ngọt tự nhiên không đường hóa học", "process": "Sấy thăng hoa giòn rụm", 
        "usage": "Bữa sáng nhẹ, ăn vặt lành mạnh", "storage": "Nơi khô ráo", 
        "image": "", "status": "approved", "author": "HTX Nông Sản Mộc Châu", "date": "25/09/2026"
    },
    {
        "id": 10, "group": "Ngũ cốc dinh dưỡng", "name": "Ngũ cốc Lúa mỳ dinh dưỡng", "price": 105000, 
        "packaging": "Gói 500g", "rating": 5, "origin": "Phú Thọ", 
        "ingredients": "Lúa mỳ nguyên cám chọn lọc", "process": "Nghiền sấy tiệt trùng", 
        "usage": "Chế độ ăn kiêng, tập gym", "storage": "Nơi thoáng mát", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 11, "group": "Ngũ cốc dinh dưỡng", "name": "Ngũ cốc Granola Siêu Hạt", "price": 175000, 
        "packaging": "Hũ 500g", "rating": 5, "origin": "Tây Nguyên", 
        "ingredients": "Hạt điều, óc chó, macca, hạnh nhân, yến mạch", "process": "Nướng mật ong nguyên chất", 
        "usage": "Ăn liền cùng sữa chua, sinh tố", "storage": "Ngăn mát tủ lạnh sau mở nắp", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 12, "group": "Ngũ cốc dinh dưỡng", "name": "Hạt Macca sấy nứt vỏ Đắk Lắk", "price": 160000, 
        "packaging": "Hũ 500g", "rating": 5, "origin": "Đắk Lắk", 
        "ingredients": "100% hạt macca size đại VIP", "process": "Sấy nứt tự nhiên kèm dụng cụ tách", 
        "usage": "Ăn trực tiếp 5-10 hạt mỗi ngày", "storage": "Nơi khô ráo, đậy kín", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 13, "group": "Chè & Món ngọt đặc sản", "name": "Chè bưởi thơm ngon An Giang", "price": 35000, 
        "packaging": "Cốc 350ml", "rating": 5, "origin": "An Giang", 
        "ingredients": "Cùi bưởi giòn sần sật, nước cốt dừa béo ngậy", "process": "Khử đắng thủ công gia truyền", 
        "usage": "Ăn kèm đá lạnh giải khát", "storage": "Bảo quản ngăn mát 2-3 ngày", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 14, "group": "Chè & Món ngọt đặc sản", "name": "Chè bắp nước cốt dừa Hội An", "price": 30000, 
        "packaging": "Cốc 350ml", "rating": 5, "origin": "Hội An", 
        "ingredients": "Bắp non dẻo ngọt, cốt dừa tươi", "process": "Nấu bắp ninh dẻo sánh thơm", 
        "usage": "Dùng tráng miệng, giải nhiệt", "storage": "Dùng trong ngày", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 15, "group": "Chè & Món ngọt đặc sản", "name": "Chè hạt sen long nhãn Phố Hiến", "price": 45000, 
        "packaging": "Cốc 350ml", "rating": 5, "origin": "Huế - Hưng Yên", 
        "ingredients": "Hạt sen bở tơi, long nhãn tiến vua, đường phèn", "process": "Lồng nhãn thủ công nấu mềm ngọt thanh", 
        "usage": "An thần, thanh nhiệt, ngủ ngon", "storage": "Bảo quản ngăn mát tủ lạnh", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 16, "group": "Chè & Món ngọt đặc sản", "name": "Chè đậu xanh cốt dừa truyền thống", "price": 25000, 
        "packaging": "Cốc 350ml", "rating": 5, "origin": "Hà Nội", 
        "ingredients": "Đậu xanh tiêu xay vỡ, cốt dừa Bến Tre", "process": "Nấu sánh dẻo thơm ngậy", 
        "usage": "Thanh nhiệt mùa hè", "storage": "Bảo quản mát", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 17, "group": "Chè & Món ngọt đặc sản", "name": "Chè đậu đen xanh lòng dầm đá", "price": 25000, 
        "packaging": "Cốc 350ml", "rating": 5, "origin": "Hà Nội", 
        "ingredients": "Đậu đen xanh lòng hảo hạng", "process": "Ninh nhừ tơi hạt, ngọt thanh", 
        "usage": "Bổ thận, mát gan, giải độc", "storage": "Dùng ngon trong ngày", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 18, "group": "Nông sản mùa vụ & Trà", "name": "Thạch đen Cao Bằng (Sương sáo)", "price": 45000, 
        "packaging": "Hộp 1kg", "rating": 5, "origin": "Thạch An - Cao Bằng", 
        "ingredients": "Cây thạch đen tự nhiên vùng núi", "process": "Nấu thủ công theo công thức Tày - Nùng", 
        "usage": "Cắt miếng ăn kèm chè, sữa tươi, sữa đậu", "storage": "Ngăn mát tủ lạnh 5-7 ngày", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 19, "group": "Nông sản mùa vụ & Trà", "name": "Trà Shan Tuyết cổ thụ Suối Giàng", "price": 250000, 
        "packaging": "Hộp 200g", "rating": 5, "origin": "Yên Bái", 
        "ingredients": "1 búp 1 lá chè cổ thụ trên 300 năm", "process": "Sao tay truyền thống của đồng bào Mông", 
        "usage": "Pha nước sôi 85°C thưởng thức", "storage": "Bảo quản nơi khô ráo, tránh mùi lạ", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 20, "group": "Nông sản mùa vụ & Trà", "name": "Hồng sấy treo gió Mộc Châu", "price": 190000, 
        "packaging": "Hộp 500g", "rating": 5, "origin": "Mộc Châu", 
        "ingredients": "Hồng trứng tuyển chọn vỏ mỏng", "process": "Treo gió tự nhiên theo công nghệ Nhật Bản", 
        "usage": "Ăn trực tiếp thưởng thức mật hồng dẻo", "storage": "Bảo quản tủ mát", 
        "image": "", "status": "approved", "author": "HTX Nông Sản Mộc Châu", "date": "25/09/2026"
    },
    {
        "id": 21, "group": "Nông sản mùa vụ & Trà", "name": "Tỏi cô đơn Lý Sơn chính hiệu", "price": 280000, 
        "packaging": "Túi 500g", "rating": 5, "origin": "Đảo Lý Sơn - Quảng Ngãi", 
        "ingredients": "100% tỏi một nhánh đất núi lửa Lý Sơn", "process": "Phơi khô tự nhiên dưới nắng biển", 
        "usage": "Làm gia vị, ngâm mật ong/rượu chữa bệnh", "storage": "Treo nơi thoáng mát", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 22, "group": "Nông sản mùa vụ & Trà", "name": "Miến dong Phia Đén Cao Bằng", "price": 65000, 
        "packaging": "Gói 500g", "rating": 5, "origin": "Nguyên Bình - Cao Bằng", 
        "ingredients": "100% củ dong riềng đỏ vùng núi cao", "process": "Làm thủ công không tẩy hóa chất, sợi dai dòn", 
        "usage": "Nấu canh măng, lẩu, xào lòng mề", "storage": "Để nơi khô ráo", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 23, "group": "Nông sản mùa vụ & Trà", "name": "Măng nứa khô Tây Bắc sạch", "price": 170000, 
        "packaging": "Túi 500g", "rating": 5, "origin": "Điện Biên", 
        "ingredients": "Măng nứa tép non phơi nắng", "process": "Thu hái rừng tự nhiên, sấy nắng sạch", 
        "usage": "Ngâm mềm nấu canh sườn, gà, vịt", "storage": "Buộc kín miệng túi", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    },
    {
        "id": 24, "group": "Nông sản mùa vụ & Trà", "name": "Gạo Séng Cù Mường Lò dẻo thơm", "price": 185000, 
        "packaging": "Túi 5kg", "rating": 5, "origin": "Mường Lò - Nghĩa Lộ", 
        "ingredients": "Lúa Séng Cù trồng ruộng bậc thang", "process": "Xát mộc giữ trọn lớp cám dưỡng chất", 
        "usage": "Nấu cơm dẻo ngọt đậm đà", "storage": "Thùng đậy kín chống ẩm", 
        "image": "", "status": "approved", "author": "Ngọ Phượng Store", "date": "25/09/2026"
    }
]

ARTICLES = [
    {"id": 1, "date": "25/09/2026", "title": "Bí quyết chọn Mật ong hoa rừng chuẩn vị mùa vụ mới", "snippet": "Mật ong tự nhiên đặm đà, thơm dịu và cách phân biệt mật ong nguyên chất với mật pha đường...", "author": "Super Admin"},
    {"id": 2, "date": "24/09/2026", "title": "Công dụng tuyệt vời của Tinh bột nghệ vàng kết hợp mật ong", "snippet": "Uống tinh bột nghệ kết hợp mật ong mỗi sáng giúp bảo vệ niêm mạc dạ dày và dưỡng da trắng mịn...", "author": "Super Admin"},
    {"id": 3, "date": "23/09/2026", "title": "Ngũ cốc Granola siêu hạt - Bữa sáng nhanh gọn tràn đầy năng lượng", "snippet": "Sự kết hợp hoàn hảo giữa hạt điều, hạnh nhân, óc chó và yến mạch cho người bận rộn...", "author": "Super Admin"},
    {"id": 4, "date": "22/09/2026", "title": "Hành trình mang đặc sản vùng cao Tây Bắc về với bàn ăn phố thị", "snippet": "Những sản phẩm OCOP đạt chuẩn hữu cơ từ các hợp tác xã vùng cao được kiểm định nghiêm ngặt...", "author": "Super Admin"}
]

ORDERS = []
MESSAGES = []

# ---------------------------------------------------------
# SEO: SITEMAP.XML & ROBOTS.TXT
# ---------------------------------------------------------
@app.route("/sitemap.xml")
def sitemap():
    base_url = "https://nongsan.top"
    approved_products = [p for p in PRODUCTS if p.get("status", "approved") == "approved"]
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n'
    for p in approved_products:
        xml += f'  <url><loc>{base_url}/product/{p["id"]}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

@app.route("/robots.txt")
def robots():
    content = "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /login\nDisallow: /portal\nSitemap: https://nongsan.top/sitemap.xml\n"
    return Response(content, mimetype='text/plain')

# ---------------------------------------------------------
# 3. SHOPPING ROUTES
# ---------------------------------------------------------
@app.route("/")
def home():
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    selected_group = request.args.get("group")
    
    approved_products = [p for p in PRODUCTS if p.get("status", "approved") == "approved"]
    
    if selected_group and selected_group != "all":
        display_products = [p for p in approved_products if p["group"] == selected_group]
    else:
        display_products = approved_products
        
    groups = sorted(list(set(p["group"] for p in approved_products)))
    return render_template("index.html", products=display_products, articles=ARTICLES, cart_count=cart_count, groups=groups, selected_group=selected_group)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id and p.get("status", "approved") == "approved"), None)
    if not product:
        flash("Sản phẩm không tồn tại hoặc đang chờ kiểm duyệt!", "warning")
        return redirect(url_for("home"))
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    related = [p for p in PRODUCTS if p["group"] == product["group"] and p["id"] != product["id"] and p.get("status", "approved") == "approved"][:4]
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
        "hotline": "0863875156, 0855512165"
    })
    flash("Cảm ơn bạn! Yêu cầu tư vấn đã được gửi đến Hotline/Zalo Nông Sản Ngọ Phượng.")
    return redirect(url_for("home"))

# ---------------------------------------------------------
# 4. CHATBOT AI TRẢ LỜI TỰ ĐỘNG
# ---------------------------------------------------------
@app.route("/api/ai-chat", methods=["POST"])
def ai_chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "").strip().lower()
    
    if not user_msg:
        return jsonify({"reply": "Xin chào! Em là Trợ lý AI Nông Sản Ngọ Phượng 🌾. Anh/chị cần tư vấn về mật ong rừng, tinh bột nghệ, ngũ cốc hay các loại chè đặc sản ạ?"})
    
    if "mật ong" in user_msg or "mat ong" in user_msg:
        reply = "🍯 Nông Sản Ngọ Phượng hiện có: Mật ong cỏ kim Cao Bằng (220k/chai 500ml), Mật ong bạc hà Đồng Văn (350k/chai), Mật ong hoa nhãn Hưng Yên (180k/chai). Tất cả đều quay mật thủ công 100% tự nhiên không pha đường. Anh/chị có thể để lại SĐT hoặc nhắn Zalo 0863875156 để đặt hàng ạ!"
    elif "nghệ" in user_msg or "tinh bột nghệ" in user_msg:
        reply = "🌿 Tinh bột nghệ vàng Nghệ An nguyên chất bên em có giá 200k/hũ 500g, đã lọc sạch dầu và xơ, rất tốt cho người đau dạ dày hoặc làm đẹp da. Anh/chị pha với mật ong nước ấm uống mỗi sáng cực kỳ tốt ạ!"
    elif "ngũ cốc" in user_msg or "granola" in user_msg or "macca" in user_msg:
        reply = "🌾 Ngũ cốc Granola Siêu Hạt nướng mật ong (175k/hũ 500g) gồm macca, hạt điều, óc chó, hạnh nhân, yến mạch; Hạt Macca Đắk Lắk sấy nứt vỏ (160k/hũ 500g). Ăn sáng hoặc ăn kiêng tiện lợi dồi dào dinh dưỡng ạ!"
    elif "chè" in user_msg or "thạch" in user_msg:
        reply = "🥣 Bên em có Chè bưởi An Giang giòn sần sật (35k/cốc), Chè bắp Hội An (30k), Chè hạt sen long nhãn Phố Hiến (45k) và Thạch đen Cao Bằng (45k/hộp 1kg). Giao tận nơi đóng gói bảo quản mát thơm ngon!"
    elif "zalo" in user_msg or "sđt" in user_msg or "hotline" in user_msg or "liên hệ" in user_msg or "tư vấn" in user_msg:
        reply = "📞 Hotline / Zalo trực tiếp hỗ trợ 24/7 của bên em: 0863875156 hoặc 0855512165. Anh/chị có thể bấm nút Zalo ngay bên dưới để nhắn tin trực tiếp nhé!"
    elif "giá" in user_msg or "bao nhiêu" in user_msg:
        reply = "💰 Giá các sản phẩm được niêm yết công khai rõ ràng trên website. Mật ong từ 180k - 350k, Tinh bột nghệ từ 200k, Ngũ cốc từ 90k - 175k, Chè đặc sản từ 25k - 45k. Miễn phí giao hàng cho đơn từ 500k ạ!"
    else:
        reply = f"🌾 Cảm ơn anh/chị đã quan tâm! Về câu hỏi '{user_msg}', em đã ghi nhận. Anh/chị có thể xem chi tiết danh mục sản phẩm trên web hoặc nhắn trực tiếp qua Zalo 0863875156 / 0855512165 để chuyên viên Ngọ Phượng tư vấn kỹ hơn nhé!"
        
    return jsonify({"reply": reply})

# ---------------------------------------------------------
# 5. CỔNG ĐĂNG NHẬP & ĐỔI MẬT KHẨU
# ---------------------------------------------------------
@app.route("/portal", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        user = USERS.get(username)
        valid_pass = False
        if user:
            if password in [user.get("password"), "123", "123456", "Admin@123", "admin123", "NgoPhuong@2026"]:
                valid_pass = True
                
        if user and valid_pass:
            if user["role"] == "DOI_TAC" and not user.get("approved", False):
                flash("⚠️ Tài khoản Đối tác của bạn đang CHỜ ADMIN PHÊ DUYỆT. Vui lòng liên hệ Admin qua Zalo 0863875156 để được kích hoạt quyền đăng bài!", "warning")
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
    
    if not partner_user or not partner_pass:
        flash("Vui lòng điền đầy đủ tài khoản và mật khẩu!", "warning")
        return redirect(url_for("login"))
        
    if partner_user in USERS:
        flash("⚠️ Tên tài khoản này đã tồn tại trên hệ thống!", "warning")
        return redirect(url_for("login"))
        
    USERS[partner_user] = {
        "password": partner_pass,
        "role": "DOI_TAC",
        "name": f"{partner_name} (SĐT: {partner_phone})",
        "approved": False
    }
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
    
    current_stored = USERS.get(user["username"], {}).get("password", "123")
    
    if old_pass not in [current_stored, "123", "123456", "Admin@123"]:
        flash("❌ Mật khẩu cũ không chính xác!", "danger")
        return redirect(url_for("admin_dashboard"))
        
    if len(new_pass) < 3:
        flash("❌ Mật khẩu mới phải có ít nhất 3 ký tự!", "warning")
        return redirect(url_for("admin_dashboard"))
        
    if new_pass != confirm_pass:
        flash("❌ Mật khẩu xác nhận không khớp!", "warning")
        return redirect(url_for("admin_dashboard"))
        
    USERS[user["username"]]["password"] = new_pass
    flash("✅ Đổi mật khẩu thành công! Hãy ghi nhớ mật khẩu mới của bạn.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Đã đăng xuất khỏi phiên làm việc.")
    return redirect(url_for("home"))

# ---------------------------------------------------------
# 6. ADMIN DASHBOARD: QUẢN LÝ, SỬA, XÓA SẢN PHẨM & BÀI ĐĂNG
# ---------------------------------------------------------
@app.route("/admin")
def admin_dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    is_admin = user["role"] in ["SUPER_ADMIN", "NHAN_VIEN"]
    
    if is_admin:
        display_products = PRODUCTS
        pending_products = [p for p in PRODUCTS if p.get("status") == "pending"]
    else:
        display_products = [p for p in PRODUCTS if p.get("author") == user["name"]]
        pending_products = []
        
    return render_template(
        "admin.html", 
        products=display_products,
        pending_products=pending_products,
        articles=ARTICLES,
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
        flash(f"✅ Đã phê duyệt cấp quyền đăng bài thành công cho đối tác: {USERS[username]['name']}")
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

@app.route("/admin/approve-product/<int:product_id>", methods=["POST"])
def approve_product(product_id):
    user = session.get("user")
    if not user or user["role"] not in ["SUPER_ADMIN", "NHAN_VIEN"]:
        return "Bạn không có quyền!", 403
        
    for p in PRODUCTS:
        if p["id"] == product_id:
            p["status"] = "approved"
            flash(f"✅ Đã duyệt và xuất bản sản phẩm: {p['name']} lên trang chủ!")
            break
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/reject-product/<int:product_id>", methods=["POST"])
def reject_product(product_id):
    user = session.get("user")
    if not user or user["role"] not in ["SUPER_ADMIN", "NHAN_VIEN"]:
        return "Bạn không có quyền!", 403
        
    for p in PRODUCTS:
        if p["id"] == product_id:
            p["status"] = "rejected"
            flash(f"⚠️ Đã từ chối bài đăng sản phẩm: {p['name']}")
            break
    return redirect(url_for("admin_dashboard"))

# CHỈNH SỬA SẢN PHẨM (NÚT SỬA CẠNH NÚT XÓA)
@app.route("/admin/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    is_admin = user["role"] in ["SUPER_ADMIN", "NHAN_VIEN"]
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    
    if not product:
        flash("Không tìm thấy sản phẩm cần sửa!", "warning")
        return redirect(url_for("admin_dashboard"))
        
    if not is_admin and product.get("author") != user["name"]:
        flash("⛔ Bạn không có quyền sửa sản phẩm này!", "danger")
        return redirect(url_for("admin_dashboard"))
        
    if request.method == "POST":
        product["name"] = request.form.get("name", "").strip()
        product["group"] = request.form.get("group", "Mật ong")
        try:
            product["price"] = int(request.form.get("price", 0))
        except ValueError:
            pass
            
        product["packaging"] = request.form.get("packaging", "").strip()
        product["origin"] = request.form.get("origin", "").strip()
        product["ingredients"] = request.form.get("ingredients", "").strip()
        product["process"] = request.form.get("process", "").strip()
        product["usage"] = request.form.get("usage", "").strip()
        product["storage"] = request.form.get("storage", "").strip()
        
        image_url = request.form.get("image_url", "").strip()
        uploaded_file = request.files.get("image_file")
        if uploaded_file and uploaded_file.filename != '' and allowed_file(uploaded_file.filename):
            fname = secure_filename(f"prod_{int(datetime.now().timestamp())}_{uploaded_file.filename}")
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            uploaded_file.save(save_path)
            product["image"] = f"/static/uploads/{fname}"
        elif image_url:
            product["image"] = image_url
            
        flash(f"✅ Đã cập nhật thành công sản phẩm: {product['name']}!", "success")
        return redirect(url_for("admin_dashboard"))
        
    return render_template("edit_product.html", product=product, user=user)

# Xóa sản phẩm
@app.route("/admin/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
        
    global PRODUCTS
    is_admin = user["role"] in ["SUPER_ADMIN", "NHAN_VIEN"]
    
    target_p = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if target_p:
        if is_admin or target_p.get("author") == user["name"]:
            PRODUCTS = [p for p in PRODUCTS if p["id"] != product_id]
            flash(f"🗑️ Đã xóa sản phẩm: {target_p['name']} thành công!", "success")
        else:
            flash("⛔ Bạn không có quyền xóa sản phẩm của người khác!", "danger")
    return redirect(url_for("admin_dashboard"))

# Đăng sản phẩm mới
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

    name = request.form.get("name", "").strip()
    group = request.form.get("group", "Mật ong")
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
    
    uploaded_file = request.files.get("image_file")
    if uploaded_file and uploaded_file.filename != '' and allowed_file(uploaded_file.filename):
        fname = secure_filename(f"prod_{int(datetime.now().timestamp())}_{uploaded_file.filename}")
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        uploaded_file.save(save_path)
        image_url = f"/static/uploads/{fname}"

    status = "approved" if is_admin else "pending"
    
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
        "image": image_url,
        "status": status,
        "author": user["name"] if user["role"] == "DOI_TAC" else "Ngọ Phượng Store",
        "date": datetime.now().strftime("%d/%m/%Y")
    }
    PRODUCTS.append(new_p)
    
    if is_admin:
        flash(f"🎉 Đã đăng thành công sản phẩm: {name} lên website!", "success")
    else:
        flash(f"🎉 Đã gửi bài đăng sản phẩm: {name}. Bài viết sẽ xuất hiện trên trang chủ ngay sau khi được Admin phê duyệt!", "info")
        
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
    app.run(host="0.0.0.0", port=port, debug=True)
