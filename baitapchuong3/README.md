# Sổ điểm lớp học - Bài tập tổng hợp Chương 3

Ứng dụng Flask: giao diện web (xem danh sách, chi tiết, tìm kiếm, xuất CSV) và API JSON (đọc, thêm/sửa, xoá điểm từng học phần). Dữ liệu lưu trong bộ nhớ (dict `STUDENTS`).

## Chạy ứng dụng

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app sodiem run --debug --port 8000
```

## 1. Kết quả `flask --app sodiem routes`

10 route (kể cả `static`):

```
Endpoint        Methods           Rule                                
--------------  ----------------  ------------------------------------
api_score       DELETE, GET, PUT  /api/students/<mssv>/scores/<course>
api_student     GET               /api/students/<mssv>                
api_students    GET               /api/students                       
export_scores   GET               /students/<mssv>/export             
home            GET               /                                   
search          GET               /search                             
short_link      GET               /sv/<mssv>                          
static          GET               /static/<path:filename>             
student_detail  GET               /students/<mssv>                    
student_list    GET               /students
```

## 2. Kết quả kiểm thử bằng curl

`B=http://127.0.0.1:8000`, `S=$B/api/students/23T1020005/scores`

| Lệnh | Dòng trạng thái | Body / header quan trọng |
|---|---|---|
| `curl -i $B/sv/23T1020001` | `301 MOVED PERMANENTLY` | `Location: /students/23T1020001` |
| `curl -i $B/students/23T1020001/export` | `200 OK` | `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename=diem_23T1020001.csv`; body: `hoc_phan,diem` / `PMMNM,8.5` / `CSDL,7.0` / `MMT,9.0` |
| `curl "$B/api/students?lop=k47a&min_avg=7"` | `200 OK` | Danh sách chỉ có `23T1020001` (Nguyễn Văn An, average 8.17, rank Khá) |
| `curl -i "$B/api/students?min_avg=abc"` | `400 BAD REQUEST` | `{"error":"Dữ liệu không hợp lệ","detail":"Tham số min_avg phải là một số."}` |
| `curl -i $B/api/students/999` | `404 NOT FOUND` | `{"error":"Không tìm thấy","detail":"Không có sinh viên với MSSV = 999."}` |
| `curl -i -X PUT "$S/web?score=9"` | `201 CREATED` | `Location: /api/students/23T1020005/scores/WEB`; body `{"mssv":"23T1020005","course":"WEB","score":9.0,"average":9.0}` |
| `curl -X PUT "$S/WEB?score=7.5"` | `200 OK` | `{"mssv":"23T1020005","course":"WEB","score":7.5,"average":7.5}` |
| `curl -i -X PUT "$S/WEB?score=11"` | `400 BAD REQUEST` | `{"error":"Dữ liệu không hợp lệ","detail":"Điểm phải nằm trong khoảng [0, 10]."}` |
| `curl -i -X DELETE $S/WEB` | `204 NO CONTENT` | Body rỗng |
| `curl -i -X POST $S/WEB` | `405 METHOD NOT ALLOWED` | `Content-Type: application/json`, `Allow: HEAD, PUT, DELETE, GET, OPTIONS`; body JSON `{"error":"Phương thức không được hỗ trợ",...}` |
| `curl -i -X POST $B/students` | `405 METHOD NOT ALLOWED` | `Content-Type: text/html; charset=utf-8`, `Allow: HEAD, GET, OPTIONS`; body là trang HTML dùng `layout()` |

Kiểm tra XSS: với `/search?q=<script>alert(1)</script>` và `/search?q="><script>alert(1)</script>`, từ khoá được `escape()` cả trong nội dung kết quả lẫn trong thuộc tính `value` của ô nhập (dấu `"` thành `&#34;`), nên trình duyệt không thực thi script. Trang 404 của `/students/<mssv>` cũng escape MSSV đưa vào thông báo lỗi.

## 3. Trả lời câu hỏi

**Vì sao dùng được `request` trong hàm xử lý lỗi (Câu 9) dù nó không phải view function?**
`request` không phải biến toàn cục thật mà là *proxy* trỏ tới request context hiện tại. Flask đẩy (push) request context ngay khi bắt đầu xử lý một request, trước khi gọi view. Khi view gọi `abort()` hoặc gặp lỗi, ngoại lệ được bắt và hàm `@app.errorhandler` được gọi *bên trong* cùng request đó, khi context vẫn còn hiệu lực. Vì vậy `request.path` trong `handle_error` trả về đúng đường dẫn của request đang lỗi. (`url_for` trong `layout()` cũng chạy được vì cùng lý do.)

**Vì sao Câu 4 dùng 301 còn Câu 8 trả 201 kèm `Location`?**
- Câu 4: `/sv/<mssv>` chỉ là địa chỉ rút gọn, tài nguyên đã *chuyển vĩnh viễn* sang `/students/<mssv>`. Mã 301 (Moved Permanently) báo cho client và công cụ tìm kiếm cập nhật, ghi nhớ địa chỉ mới; `Location` chỉ nơi cần đến.
- Câu 8: PUT tạo ra một tài nguyên *mới* (điểm học phần chưa có), không có chuyện "chuyển đi đâu". Mã 201 (Created) báo đã tạo thành công; `Location` cho client biết URL của tài nguyên vừa tạo để dùng tiếp (GET, PUT, DELETE).

**Thêm điểm cho 23T1020005 rồi khởi động lại server, điểm đó còn không? Vì sao?**
Không còn. Dữ liệu chỉ nằm trong dict `STUDENTS` trong bộ nhớ của tiến trình Python. Khi server tắt, tiến trình kết thúc và bộ nhớ bị giải phóng; khởi động lại thì `STUDENTS` được nạp lại từ mã nguồn với dữ liệu mẫu ban đầu. Đã kiểm chứng: trước khi restart `GET .../scores/WEB` trả 200, sau khi restart trả 404. Muốn lưu bền cần ghi ra file hoặc dùng cơ sở dữ liệu. (Ngoài ra, với `--debug`, mỗi lần sửa mã server cũng tự khởi động lại và dữ liệu cũng mất.)
