# Mass Ban Tool (Selfbot)
> công cụ giúp bạn ban hàng loạt member của server sử dụng chính tài khoản của bạn
Bán là con đĩ mẹ mày chết đéo có chỗ chôn xác - dùng free đéo star chết nốt

--

Cách dùng:
1. pip install -r requirements.txt — cài thư viện
2. Chạy python massban.py
3. Menu tương tác:
- 1 → Mass Ban
- 2 → Mass Kick
4. Nhập token(s) (user token Discord, cách nhau bằng space/comma, có thể nhiều token để chia tải)
5. Nhập Guild ID (bật Developer Mode → chuột phải server → Copy ID)
6. Nhập proxy (tùy chọn, định dạng http://user:pass@ip:port, Enter để bỏ qua)
7. Nhập workers per token (mặc định 15, tối đa 100)
Cần chuẩn bị:
- Python 3.10+
- Token Discord user (lấy từ Authorization header khi F12 vào Discord web)
- Token cần quyền Ban Members (ban) hoặc Kick Members (kick) trong server
- Proxy khuyến nghị dùng để tránh rate limit (càng nhiều proxy/token càng tốt)

---
<img width="1721" height="805" alt="image" src="https://github.com/user-attachments/assets/99d54984-0e6e-4925-8817-3e456962c791" />
