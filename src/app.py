import importlib
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from models import Customer, TermSaving, NonTermSaving
import database as db

# Tự động nạp lại module database để tránh lỗi cache AttributeError của Streamlit
importlib.reload(db)

st.set_page_config(page_title="Hệ Thống Tiết Kiệm Ngân Hàng", page_icon="🏦", layout="wide")
db.init_db()

st.markdown("""
    <style>
    .stDeployButton {display:none;}
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #1d5d9b;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .main-header {
        background: linear-gradient(90deg, #0f2c59 0%, #1d5d9b 100%);
        color: white;
        padding: 18px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .main-header h2 {
        color: white !important;
        margin: 0;
        font-size: 24px;
    }
    .main-header p {
        color: #e2e8f0;
        margin: 4px 0 0 0;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

RATE_TABLE = {0: 0.5, 1: 3.2, 3: 3.8, 6: 5.2, 12: 6.0, 24: 6.5}

with st.sidebar:
    st.markdown("## 🏦 NGÂN HÀNG SỐ")
    st.caption("Hệ thống Quản lý Tiền gửi Tiết kiệm")
    st.divider()
    menu = st.radio(
        "DANH MỤC NGHIỆP VỤ:",
        [
            "📊 Tổng quan (Dashboard)",
            "👤 Quản lý Khách hàng (Thêm/Sửa)",
            "➕ Mở sổ tiết kiệm",
            "💰 Tất toán & Rút tiền",
            "🗑️ Xóa sổ tiết kiệm nhập sai",
            "🧮 Công cụ tính lãi giả định"
        ]
    )
    st.divider()
    next_preview_id = db.get_next_acc_id()
    st.info(f"📌 **Mã sổ cấp tiếp theo:** `{next_preview_id}`")

df_all = db.get_all_savings_df()
df_cust = db.get_all_customers_df()

# ================= 1. DASHBOARD =================
if menu == "📊 Tổng quan (Dashboard)":
    st.markdown("""
        <div class="main-header">
            <h2>📊 Bảng Điều Khiển Quản Lý Tiền Gửi Tiết Kiệm</h2>
            <p>Theo dõi số liệu huy động vốn, cơ cấu kỳ hạn và tra cứu danh sách sổ tiết kiệm theo thời gian thực</p>
        </div>
    """, unsafe_allow_html=True)

    df_active = df_all[df_all["status"] == "Đang hoạt động"]
    total_money = df_active["amount"].sum() if not df_active.empty else 0
    total_books = len(df_active)
    total_customers = len(df_cust)

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Tổng vốn huy động (Đang gửi)", f"{total_money:,.0f} VNĐ")
    col2.metric("📘 Số sổ đang hoạt động", f"{total_books} sổ")
    col3.metric("👥 Tổng số khách hàng đã đăng ký", f"{total_customers} người")

    st.write("")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        with st.container(border=True):
            if not df_active.empty:
                df_active_copy = df_active.copy()
                df_active_copy["Kỳ hạn"] = df_active_copy["term_months"].apply(
                    lambda x: "Không kỳ hạn" if x == 0 else f"{x} tháng"
                )
                fig = px.pie(
                    df_active_copy, values="amount", names="Kỳ hạn",
                    title="Tỷ trọng tiền gửi đang hoạt động theo kỳ hạn",
                    hole=0.35
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu sổ đang hoạt động để vẽ biểu đồ.")

    with col_chart2:
        with st.container(border=True):
            if not df_all.empty:
                fig2 = px.bar(
                    df_all, x="full_name", y="amount", color="status",
                    title="Thống kê số tiền gửi theo Khách hàng",
                    labels={"full_name": "Khách hàng", "amount": "Số tiền (VNĐ)", "status": "Trạng thái"}
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu sổ tiết kiệm.")

    with st.container(border=True):
        st.subheader("📋 Danh sách sổ tiết kiệm trên hệ thống")
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search = st.text_input("🔍 Tìm kiếm nhanh theo Họ tên, Số CCCD, Số điện thoại hoặc Mã sổ:")
        with col_filter:
            status_filter = st.selectbox("Lọc theo trạng thái:", ["Tất cả", "Đang hoạt động", "Đã tất toán"])

        df_display = df_all.copy()
        if status_filter != "Tất cả":
            df_display = df_display[df_display["status"] == status_filter]

        if search:
            df_display = df_display[
                df_display["full_name"].str.contains(search, case=False) |
                df_display["cccd"].str.contains(search, case=False) |
                df_display["phone"].str.contains(search, case=False) |
                df_display["acc_id"].str.contains(search, case=False)
            ]

        df_vn = df_display.rename(columns={
            "acc_id": "Mã sổ",
            "cccd": "Số CCCD",
            "full_name": "Họ và tên",
            "phone": "Số điện thoại",
            "address": "Địa chỉ",
            "amount": "Số tiền gửi (VNĐ)",
            "open_date": "Ngày mở sổ",
            "term_months": "Kỳ hạn (Tháng)",
            "interest_rate": "Lãi suất (%/năm)",
            "status": "Trạng thái"
        })

        st.dataframe(
            df_vn,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Số tiền gửi (VNĐ)": st.column_config.NumberColumn(format="%d VNĐ")
            }
        )

        csv = df_vn.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Xuất danh sách ra Excel / CSV", data=csv, file_name="danh_sach_tiet_kiem.csv", mime="text/csv")

# ================= 2. QUẢN LÝ KHÁCH HÀNG (THÊM / SỬA) =================
elif menu == "👤 Quản lý Khách hàng (Thêm/Sửa)":
    st.markdown("""
        <div class="main-header">
            <h2>👤 Quản Lý Hồ Sơ Khách Hàng</h2>
            <p>Đăng ký thông tin khách hàng mới (kiểm tra chi tiết chống trùng CCCD & SĐT) và cập nhật hồ sơ khách hàng</p>
        </div>
    """, unsafe_allow_html=True)

    if "cust_success" in st.session_state:
        st.success(st.session_state.pop("cust_success"))

    tab_add, tab_edit = st.tabs(["➕ Thêm khách hàng mới", "✏️ Chỉnh sửa thông tin khách hàng"])

    with tab_add:
        with st.form("add_customer_form", clear_on_submit=False):
            st.markdown("#### Nhập hồ sơ khách hàng mới")
            c1, c2 = st.columns(2)
            with c1:
                cccd = st.text_input("Số CCCD (Đúng 12 chữ số) *", max_chars=12, placeholder="VD: 056204009999")
                full_name = st.text_input("Họ và tên khách hàng *", placeholder="VD: Đào Xuân Thành")
            with c2:
                phone = st.text_input("Số điện thoại (Đúng 10 chữ số) *", max_chars=10, placeholder="VD: 0905123456")
                address = st.text_input("Địa chỉ thường trú", placeholder="VD: Nha Trang, Khánh Hòa")

            btn_add_cust = st.form_submit_button("✅ Lưu Hồ Sơ Khách Hàng", type="primary", use_container_width=True)

            if btn_add_cust:
                cccd_clean = cccd.strip()
                name_clean = full_name.strip()
                phone_clean = phone.strip()
                addr_clean = address.strip()

                errors = []
                # 1. Kiểm tra chi tiết Số CCCD
                if not cccd_clean:
                    errors.append("⚠️ **Lỗi để trống CCCD:** Vui lòng nhập Số Căn cước công dân (12 chữ số).")
                elif not cccd_clean.isdigit():
                    errors.append(f"⚠️ **Lỗi định dạng CCCD:** Giá trị `{cccd_clean}` có chứa chữ cái hoặc ký tự đặc biệt. CCCD chỉ được phép chứa các chữ số (0-9).")
                elif len(cccd_clean) != 12:
                    errors.append(f"⚠️ **Lỗi độ dài CCCD:** Bạn mới nhập **{len(cccd_clean)}/12** chữ số (`{cccd_clean}`). Vui lòng nhập đủ đúng 12 chữ số.")
                else:
                    existing_cust = db.get_customer_by_cccd(cccd_clean)
                    if existing_cust:
                        errors.append(
                            f"❌ **Lỗi trùng Số CCCD:** Số CCCD `{cccd_clean}` đã được đăng ký cho khách hàng "
                            f"**{existing_cust['full_name']}** (SĐT: `{existing_cust['phone']}`, Địa chỉ: {existing_cust['address']}). "
                            f"Vui lòng kiểm tra lại hoặc sang mục **➕ Mở sổ tiết kiệm** để mở sổ cho khách hàng này!"
                        )

                # 2. Kiểm tra chi tiết Họ và tên
                if not name_clean:
                    errors.append("⚠️ **Lỗi để trống Họ tên:** Vui lòng nhập đầy đủ Họ và tên của khách hàng.")
                elif len(name_clean) < 2:
                    errors.append("⚠️ **Lỗi Họ tên quá ngắn:** Họ và tên khách hàng phải có ít nhất 2 ký tự.")

                # 3. Kiểm tra chi tiết Số điện thoại
                if not phone_clean:
                    errors.append("⚠️ **Lỗi để trống Số điện thoại:** Vui lòng nhập số điện thoại liên hệ (10 chữ số).")
                elif not phone_clean.isdigit():
                    errors.append(f"⚠️ **Lỗi định dạng Số điện thoại:** Giá trị `{phone_clean}` chứa ký tự không phải chữ số.")
                elif not phone_clean.startswith("0"):
                    errors.append(f"⚠️ **Lỗi đầu số điện thoại:** Số điện thoại `{phone_clean}` phải bắt đầu bằng chữ số **0** (VD: 09..., 03..., 07..., 08...).")
                elif len(phone_clean) != 10:
                    errors.append(f"⚠️ **Lỗi độ dài Số điện thoại:** Bạn mới nhập **{len(phone_clean)}/10** chữ số (`{phone_clean}`). Số điện thoại Việt Nam phải có đúng 10 chữ số.")
                else:
                    existing_phone = db.get_customer_by_phone(phone_clean)
                    if existing_phone:
                        errors.append(
                            f"❌ **Lỗi trùng Số điện thoại:** Số điện thoại `{phone_clean}` đang được sử dụng bởi khách hàng "
                            f"**{existing_phone['full_name']}** (CCCD: `{existing_phone['cccd']}`)."
                        )

                if errors:
                    st.error("🚨 **KHÔNG THỂ LƯU HỒ SƠ! Vui lòng kiểm tra các lỗi cụ thể sau:**")
                    for err in errors:
                        st.markdown(f"- {err}")
                else:
                    new_cust = Customer(cccd_clean, name_clean.title(), phone_clean, addr_clean)
                    db.add_customer(new_cust)
                    st.session_state["cust_success"] = (
                        f"🎉 **THÊM KHÁCH HÀNG THÀNH CÔNG!**\n\n"
                        f"- **Họ và tên:** {name_clean.title()}\n"
                        f"- **Số CCCD:** `{cccd_clean}`\n"
                        f"- **Số điện thoại:** `{phone_clean}`\n"
                        f"- **Địa chỉ:** {addr_clean if addr_clean else 'Chưa cập nhật'}\n\n"
                        f"👉 Bạn có thể chuyển sang mục **➕ Mở sổ tiết kiệm** ở menu bên trái để mở sổ cho khách hàng này."
                    )
                    st.rerun()

    with tab_edit:
        if df_cust.empty:
            st.info("Chưa có dữ liệu khách hàng.")
        else:
            with st.container(border=True):
                cust_options = {
                    f"{row['cccd']} - {row['full_name']} (SĐT: {row['phone']})": row
                    for _, row in df_cust.iterrows()
                }
                selected_cust_label = st.selectbox("Chọn khách hàng cần chỉnh sửa:", list(cust_options.keys()))
                selected_cust = cust_options[selected_cust_label]

                with st.form("edit_customer_form"):
                    st.text_input("Số CCCD (Khóa chính - Không thay đổi)", value=selected_cust["cccd"], disabled=True)
                    new_name = st.text_input("Họ và tên *", value=selected_cust["full_name"])
                    new_phone = st.text_input("Số điện thoại (Đúng 10 chữ số) *", value=selected_cust["phone"], max_chars=10)
                    new_addr = st.text_input("Địa chỉ", value=selected_cust["address"])
                    btn_update = st.form_submit_button("💾 Lưu Thay Đổi Hồ Sơ", type="primary", use_container_width=True)

                    if btn_update:
                        phone_clean = new_phone.strip()
                        name_clean = new_name.strip()
                        edit_errors = []

                        if not name_clean:
                            edit_errors.append("⚠️ **Lỗi để trống Họ tên:** Họ tên khách hàng không được để trống.")
                        if not phone_clean.isdigit() or not phone_clean.startswith("0") or len(phone_clean) != 10:
                            edit_errors.append(f"⚠️ **Lỗi Số điện thoại (`{phone_clean}`):** Phải bắt đầu bằng số **0** và có đúng **10 chữ số** (Hiện tại: {len(phone_clean)} ký tự).")
                        else:
                            dup_phone = db.get_customer_by_phone(phone_clean, exclude_cccd=selected_cust["cccd"])
                            if dup_phone:
                                edit_errors.append(f"❌ **Lỗi trùng Số điện thoại:** SĐT `{phone_clean}` đã thuộc về khách hàng **{dup_phone['full_name']}** (CCCD: `{dup_phone['cccd']}`).")

                        if edit_errors:
                            for e in edit_errors:
                                st.error(e)
                        else:
                            db.update_customer(selected_cust["cccd"], name_clean.title(), phone_clean, new_addr.strip())
                            st.session_state["cust_success"] = (
                                f"✅ **CẬP NHẬT HỒ SƠ THÀNH CÔNG!**\n\n"
                                f"Khách hàng **{name_clean.title()}** (CCCD: `{selected_cust['cccd']}`) đã được cập nhật SĐT thành `{phone_clean}` và địa chỉ thành `{new_addr.strip()}`."
                            )
                            st.rerun()

    st.write("")
    with st.container(border=True):
        st.subheader("📋 Danh sách Khách hàng hiện có")
        df_cust_vn = df_cust.rename(columns={
            "cccd": "Số CCCD",
            "full_name": "Họ và tên",
            "phone": "Số điện thoại",
            "address": "Địa chỉ",
            "total_books": "Số lượng sổ đã mở"
        })
        st.dataframe(df_cust_vn, use_container_width=True, hide_index=True)

# ================= 3. MỞ SỔ TIẾT KIỆM =================
elif menu == "➕ Mở sổ tiết kiệm":
    st.markdown("""
        <div class="main-header">
            <h2>➕ Mở Sổ Tiết Kiệm Mới</h2>
            <p>Chọn khách hàng từ danh sách đã đăng ký để mở sổ tiết kiệm mới (Mã sổ tự động lấp đầy khoảng trống)</p>
        </div>
    """, unsafe_allow_html=True)

    if "saving_success" in st.session_state:
        st.success(st.session_state.pop("saving_success"))

    if df_cust.empty:
        st.warning("⚠️ Hệ thống chưa có khách hàng nào! Vui lòng vào mục **👤 Quản lý Khách hàng** để thêm khách hàng trước.")
    else:
        auto_acc_id = db.get_next_acc_id()

        with st.container(border=True):
            st.markdown("#### 👤 Bước 1: Chọn khách hàng đứng tên sổ")
            cust_map = {
                f"{row['cccd']} - {row['full_name']} (SĐT: {row['phone']} | Đang có: {row['total_books']} sổ)": row
                for _, row in df_cust.iterrows()
            }
            chosen_label = st.selectbox(
                "Tìm hoặc chọn khách hàng trong danh sách (Gõ tên hoặc CCCD để tìm nhanh):",
                options=list(cust_map.keys())
            )
            chosen_cust = cust_map[chosen_label]

            c_info1, c_info2, c_info3 = st.columns(3)
            c_info1.info(f"**Họ và tên:** {chosen_cust['full_name']}")
            c_info2.info(f"**Số CCCD:** `{chosen_cust['cccd']}`")
            c_info3.info(f"**SĐT:** {chosen_cust['phone']} | **Đ/c:** {chosen_cust['address']}")

        with st.form("open_saving_only_form", clear_on_submit=False):
            st.markdown("#### 📘 Bước 2: Nhập thông tin sổ tiết kiệm")
            col1, col2 = st.columns(2)
            with col1:
                st.text_input(
                    "Mã sổ tiết kiệm (Tự động sinh - Không chỉnh sửa)",
                    value=auto_acc_id,
                    disabled=True,
                    help="Hệ thống tự động chọn mã số nhỏ nhất còn trống (VD: xóa STK003 thì sổ mới sẽ lấy lại mã STK003)"
                )
                amount = st.number_input(
                    "Số tiền gửi (VNĐ) - Tối thiểu 1.000.000 *",
                    min_value=1000000.0, value=10000000.0, step=1000000.0
                )
            with col2:
                term = st.selectbox(
                    "Kỳ hạn gửi (Tháng) *",
                    options=list(RATE_TABLE.keys()),
                    format_func=lambda x: "Không kỳ hạn (0.5%/năm)" if x == 0 else f"{x} tháng (Lãi suất {RATE_TABLE[x]}%/năm)"
                )
                open_date = st.date_input("Ngày mở sổ *", value=datetime.today())

            st.write("")
            submitted = st.form_submit_button("✅ Xác Nhận Mở Sổ Tiết Kiệm", type="primary", use_container_width=True)

            if submitted:
                if db.check_acc_id_exists(auto_acc_id):
                    st.error(f"❌ **Lỗi trùng mã sổ tiết kiệm:** Mã sổ `{auto_acc_id}` đã tồn tại trên hệ thống! Vui lòng tải lại trang.")
                else:
                    rate = RATE_TABLE[term]
                    date_str = open_date.strftime("%Y-%m-%d")
                    cccd_selected = chosen_cust["cccd"]
                    term_label = "Không kỳ hạn" if term == 0 else f"{term} tháng"

                    if term == 0:
                        saving_obj = NonTermSaving(auto_acc_id, cccd_selected, amount, date_str, rate)
                    else:
                        saving_obj = TermSaving(auto_acc_id, cccd_selected, amount, date_str, term, rate)

                    try:
                        db.add_saving(saving_obj)
                        st.session_state["saving_success"] = (
                            f"🎉 **MỞ SỔ TIẾT KIỆM THÀNH CÔNG!**\n\n"
                            f"- **Mã sổ tiết kiệm:** `{auto_acc_id}`\n"
                            f"- **Chủ sở hữu:** {chosen_cust['full_name']} (CCCD: `{cccd_selected}`)\n"
                            f"- **Số tiền gửi gốc:** **{amount:,.0f} VNĐ**\n"
                            f"- **Kỳ hạn & Lãi suất:** {term_label} (**{rate}%/năm**)\n"
                            f"- **Ngày mở sổ:** {date_str}"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ **Lỗi hệ thống khi lưu sổ tiết kiệm:** Chi tiết lỗi: `{e}`")

# ================= 4. TẤT TOÁN & RÚT TIỀN =================
elif menu == "💰 Tất toán & Rút tiền":
    st.markdown("""
        <div class="main-header">
            <h2>💰 Tính Lãi & Tất Toán Sổ Tiết Kiệm</h2>
            <p>Tự động đối chiếu số ngày thực gửi với kỳ hạn cam kết để tính lãi đúng hạn hoặc phạt rút trước hạn</p>
        </div>
    """, unsafe_allow_html=True)

    active_df = df_all[df_all["status"] == "Đang hoạt động"]
    if active_df.empty:
        st.info("Hiện không có sổ tiết kiệm nào đang hoạt động để tất toán.")
    else:
        with st.container(border=True):
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                book_options = {
                    f"{row['acc_id']} - {row['full_name']} ({row['amount']:,.0f} VNĐ)": row["acc_id"]
                    for _, row in active_df.iterrows()
                }
                selected_label = st.selectbox("📌 Chọn Sổ tiết kiệm cần kiểm tra / tất toán:", list(book_options.keys()))
                selected_id = book_options[selected_label]
            with col_sel2:
                close_date = st.date_input("📅 Ngày dự kiến rút / tất toán:", value=datetime.today())

        saving_obj = db.get_saving_object(selected_id)
        if saving_obj:
            result = saving_obj.calculate_interest(close_date.strftime("%Y-%m-%d"))

            st.markdown("### 🧾 Phiếu Tạm Tính Chi Tiết Tất Toán")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💵 Tiền gốc ban đầu", f"{saving_obj.amount:,.0f} VNĐ")
            c2.metric("⏱️ Số ngày thực gửi", f"{result['days']} ngày")
            c3.metric("📈 Tiền lãi thực nhận", f"{result['interest']:,.0f} VNĐ")
            c4.metric("💰 TỔNG CHI TRẢ", f"{result['total']:,.0f} VNĐ")

            st.warning(f"📌 **Quy tắc áp dụng:** {result['note']}")

            if st.button("✅ Xác Nhận Tất Toán & Đóng Sổ Này", type="primary", use_container_width=True):
                db.close_saving_account(selected_id)
                st.success(f"🎉 **TẤT TOÁN THÀNH CÔNG!** Sổ `{selected_id}` đã chuyển sang trạng thái **Đã tất toán**. Tổng số tiền chi trả cho khách hàng: **{result['total']:,.0f} VNĐ**.")
                st.rerun()

# ================= 5. XÓA SỔ TIẾT KIỆM =================
elif menu == "🗑️ Xóa sổ tiết kiệm nhập sai":
    st.markdown("""
        <div class="main-header">
            <h2>🗑️ Xóa Sổ Tiết Kiệm Nhập Sai</h2>
            <p>Xóa sổ tiết kiệm bị nhập nhầm khỏi hệ thống (Mã sổ bị xóa sẽ tự động được cấp lại cho sổ mở mới tiếp theo)</p>
        </div>
    """, unsafe_allow_html=True)

    if "del_success" in st.session_state:
        st.success(st.session_state.pop("del_success"))

    if df_all.empty:
        st.info("Chưa có sổ tiết kiệm nào trong hệ thống.")
    else:
        with st.container(border=True):
            del_options = {
                f"{row['acc_id']} | KH: {row['full_name']} (CCCD: {row['cccd']}) | Tiền gửi: {row['amount']:,.0f} VNĐ ({row['status']})": row
                for _, row in df_all.iterrows()
            }
            selected_del_label = st.selectbox("Chọn sổ tiết kiệm muốn xóa:", list(del_options.keys()))
            del_row = del_options[selected_del_label]
            del_acc_id = del_row["acc_id"]

            st.info(f"💡 Sau khi xóa sổ **{del_acc_id}**, mã **`{del_acc_id}`** sẽ tự động được ưu tiên cấp lại khi bạn mở sổ mới để lấp đầy khoảng trống.")
            if st.button(f"🗑️ Xác Nhận Xóa Sổ {del_acc_id}", type="primary"):
                db.delete_saving_account(del_acc_id)
                st.session_state["del_success"] = (
                    f"✅ **ĐÃ XÓA SỔ TIẾT KIỆM THÀNH CÔNG!**\n\n"
                    f"- **Mã sổ vừa xóa:** `{del_acc_id}` (Khách hàng: **{del_row['full_name']}** - Số tiền: **{del_row['amount']:,.0f} VNĐ**)\n"
                    f"- **Trạng thái cấp mã:** Mã `{del_acc_id}` đã được giải phóng và sẽ tự động gán cho sổ mở mới tiếp theo!"
                )
                st.rerun()

# ================= 6. CÔNG CỤ TÍNH LÃI GIẢ ĐỊNH =================
elif menu == "🧮 Công cụ tính lãi giả định":
    st.markdown("""
        <div class="main-header">
            <h2>🧮 Công Cụ Ước Tính Lãi Suất Cho Khách Hàng</h2>
            <p>Kéo thanh trượt để so sánh nhanh số tiền lãi nhận được ở từng kỳ hạn gửi khác nhau</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        sim_amount = st.slider(
            "💵 Chọn số tiền khách hàng dự định gửi (VNĐ):",
            min_value=5000000, max_value=1000000000, value=100000000, step=5000000,
            format="%d VNĐ"
        )
        st.markdown(f"**Số tiền gốc mô phỏng:** :blue[**{sim_amount:,.0f} VNĐ**]")

        sim_data = []
        for term, rate in RATE_TABLE.items():
            if term > 0:
                days = term * 30
                interest = sim_amount * (rate / 100) * (days / 365)
                sim_data.append({
                    "Kỳ hạn gửi": f"{term} tháng ({days} ngày)",
                    "Lãi suất niêm yết": f"{rate}% / năm",
                    "Tiền lãi dự kiến (VNĐ)": f"+ {interest:,.0f} VNĐ",
                    "Tổng nhận khi đáo hạn (VNĐ)": f"{sim_amount + interest:,.0f} VNĐ"
                })
        st.table(pd.DataFrame(sim_data))