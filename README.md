# 🎮 AI Maze Quest — Robot thoát mê cung (12 Thuật Toán AI)

**AI Maze Quest** là một trò chơi mê cung giải cứu đa tác nhân kịch tính được viết bằng ngôn ngữ Python sử dụng thư viện đồ họa **PyQt5**. Dự án này được thiết kế như một sản phẩm đồ án hoàn chỉnh môn **Trí tuệ Nhân tạo (Artificial Intelligence)**, tích hợp đồng bộ **trọn vẹn 12 thuật toán AI kinh điển (thuộc 6 nhóm chủ đề)** trực tiếp vào các cơ chế vận hành thời gian thực của game.

Giao diện trò chơi được tối ưu hóa theo phong cách tối giản hiện đại (Sleek Dark Mode Sci-Fi), tích hợp hiệu ứng **Mô phỏng đục tường & tô màu trực quan 4 giai đoạn** cùng bảng **Nhật ký hệ thống AI** thời gian thực để giảng viên dễ dàng đối chứng và đánh giá.

---

## 📁 1. Cấu trúc Thư mục Dự án

Mã nguồn được phân tách theo mô hình phát triển phần mềm chuyên nghiệp:
* 📄 **game_models.py**: Chứa các định nghĩa cấu trúc dữ liệu trò chơi (`GridMap`, `TicTacToe`, `MapColoringCSP`).
* 📄 **algorithms.py**: Chứa mã nguồn của cả 12 thuật toán AI và cơ chế tối ưu hóa A* Cache.
* 📄 **main.py**: File chạy chính, xử lý giao diện đồ họa PyQt5, vẽ lưới mê cung, các cửa sổ phân tích AI và game loop.

---

## ⚙️ 2. Hướng dẫn Cài đặt & Khởi chạy

### Yêu cầu hệ thống:
* **Python 3.9+**
* Thư viện **PyQt5**.

### Cài đặt nhanh:
Mở Terminal tại thư mục dự án và chạy lệnh cài đặt thư viện:
```powershell
pip install PyQt5
```

### Khởi chạy Game:
Chạy tệp tin `main.py` bằng trình thông dịch Python trên máy của bạn:
```powershell
py main.py
```

---

## 🎮 3. Hướng dẫn Điều khiển & Cơ chế Trò chơi

### Cách điều khiển:
| Phím điều khiển / Thao tác | Hành động trong game |
| :--- | :--- |
| **↑ ↓ ← →** hoặc **W A S D** | Di chuyển Robot cứu hộ **🤖** đi 1 ô theo hướng tương ứng |
| **R** hoặc nút **Game Mới** | Khởi chạy quá trình khởi tạo & mô phỏng tạo mê cung mới |
| **Nhấp dòng trên Cây Dự Phòng** | Highlight ô tương ứng trên mê cung bằng viền Neon Magenta `#FF00FF` & mục tiêu `🎯` |

### Tiến trình Khởi tạo Mê cung Trực quan (4 Giai đoạn):
Mỗi khi khởi động hoặc ấn **Game Mới (R)**, trò chơi sẽ trình diễn mô phỏng thuật toán qua 4 giai đoạn:
1. **Giai đoạn 1 (Full Tường 🧱):** Khởi tạo bản đồ phủ kín 100% bằng khối tường 3D Firewall `#`.
2. **Giai đoạn 2 (DFS Đục Tường ⚡):** Thuật toán DFS Recursive Backtracker đào từng ô đường đi trên nền tối trung tính (`#141a29`). Con trỏ tia sét `⚡` lướt đào tường theo thời gian thực (không tô sẵn màu).
3. **Giai đoạn 3 (Trực quan CSP & Tô Màu Địa Hình 🎨):**
   * **Phân màu 6 phân vùng CSP bằng Min-Conflicts:** Hiển thị bản màu ngẫu nhiên ban đầu (Bước 1), sau đó thuật toán Min-Conflicts tự động tìm và sửa mâu thuẫn màu giáp ranh từng bước một trực quan (Bước 2..N).
   * **Sơn địa hình Bùn & Băng:** Phủ lần lượt từng ô Bùn `🐾` và Băng `❄️` với biểu tượng lấp lánh `✨` trên nền các phân vùng.
4. **Giai đoạn 4 (Khởi tạo Thực thể 🤖🚪🤕👮‍♂️):** Xuất hiện Robot `🤖`, Lối ra `🚪`, 3 Nạn nhân `🤕` và các Cảnh sát `👮‍♂️` `👻`.

### Luật chơi chi tiết:
1. **Mục tiêu tối thượng:** Điều khiển Robot **🤖** di chuyển giải cứu **3 nạn nhân 🤕**, sau đó di chuyển tới ô Cửa thoát hiểm **🚪** để giành chiến thắng.
2. **Cơ chế địa hình:**
   * Bùn lầy **Mud `🐾` (màu nâu `#5D4037`)**: Chi phí di chuyển = **3 bước**.
   * Vũng băng trơn **Ice `❄️` (gradient xanh)**: 50% khả năng trượt chân ngẫu nhiên sang ô bên cạnh.
3. **Hệ thống Bảo vệ & Stalker:**
   * **Bảo vệ A* `👮‍♂️` (viền đỏ):** Đuổi bắt bằng thuật toán A* Search (né vũng bùn).
   * **Bảo vệ Greedy `👮‍♂️` (viền cam):** Đuổi bắt nhanh bằng Greedy Best-First Search.
   * **Stalker `👻` (viền tím):** Agent mù đi săn Robot dựa trên cảm biến ngửi mùi bán kính 3 ô (Belief State Tracking).
4. **Cơ chế Vùng chiến thuật (CSP Gameplay):**
   * 🔴 **Vùng Đỏ (Báo động):** Bảo vệ di chuyển tốc độ bình thường.
   * 🔵 **Vùng Lam (Gây nhiễu):** Bảo vệ bị làm chậm (chỉ di chuyển 1 ô sau mỗi 2 bước của bạn).
   * 🟢 **Vùng Lục (An toàn):** Robot hoàn toàn miễn nhiễm bị bắt.
5. **Màn đấu trí caro khi bị bắt (Duel Minigame) & Mạng sống:**
   * Nếu bị bắt, đối đầu với AI trong game Caro 3x3 (Minimax / Alpha-Beta Pruning). Thắng/Hòa hạ gục bảo vệ vĩnh viễn, Thua bị mất 1 mạng. Sau khi mất 1 mạng, thuật toán **Backtracking Search CSP** sẽ tự động đệ quy quay lui tái cấu trúc màu sắc các phân vùng an toàn.
6. **Cửa sổ Cây Kế hoạch Dự phòng (AND-OR Search):**
   * Nhấp nút "Kế Hoạch Vượt Băng" để mở cây dự phòng bao quát mọi rủi ro trượt ngã trên băng. Nhấp vào bất kỳ nút dòng nào trên cây sẽ tự động khoanh vùng và highlight ô đó trên mê cung.

---

## 🧠 4. Cách Áp dụng 12 Thuật toán AI trong Game

### Nhóm 1: Tìm kiếm không có thông tin (Uninformed Search)

* **1. DFS (Depth-First Search):** Áp dụng Recursive Backtracker đục tường mê cung ngẫu nhiên liên thông (kèm bước phá 15% tường tạo đa lối đi). Trực quan hóa bằng tia sét `⚡`.

  <video src="https://github.com/user-attachments/assets/33942147-bd98-4282-a30c-819076379bc9" controls muted width="700"></video>

* **2. BFS (Breadth-First Search):** Loang chiều rộng tính toán **Trường khoảng cách** từ Lối ra `🚪` tới mọi ô trống trên bản đồ theo thời gian thực.

  <img width="700" alt="BFS Distance Field" src="https://github.com/user-attachments/assets/ea1c72fc-fd9b-4661-9c90-682a30c1f582" />

---

### Nhóm 2: Tìm kiếm có thông tin (Informed / Heuristic Search)

* **3. A\* Search:** Điều khiển **Bảo vệ A*** và **Stalker** tìm đường đuổi bắt tối ưu qua hàm đánh giá $f(n)=g(n)+h(n)$ (biết chủ động đi vòng né ô Bùn `🐾`).

  <video src="https://github.com/user-attachments/assets/9dc03160-9275-4d21-be61-669101e8e2dc" controls muted width="700"></video>

* **4. Greedy Best-First Search:** Điều khiển **Bảo vệ Greedy** nhắm thẳng hướng Robot bằng hàm heuristic $h(n)$ (Khoảng cách Manhattan).

  <video src="https://github.com/user-attachments/assets/bfa48ed0-15db-4174-9a44-795305c10f74" controls muted width="700"></video>

---

### Nhóm 3: Tìm kiếm cục bộ (Local Search)

* **5. Simple Hill Climbing:** Leo đồi cơ bản chọn nước đi tốt hơn đầu tiên để vận hành tính năng **Đi Tự Động (Auto-Step)**.

  <img width="700" alt="Simple Hill Climbing" src="https://github.com/user-attachments/assets/78f3c7ac-cde0-44f0-937c-8691d5564300" />

* **6. Steepest-Ascent Hill Climbing:** Leo đồi dốc đứng duyệt toàn bộ hàng xóm để vẽ ra **Lộ trình GPS** tối ưu nhất (chuỗi mũi tên Neon Sci-Fi Cyan `▲▼◄►`).

  <video src="https://github.com/user-attachments/assets/8c639506-b5cd-43e1-bddb-9b0eb5abd911" controls muted width="700"></video>

---

### Nhóm 4: Tìm kiếm trong môi trường phức tạp (Complex Environments)

* **7. Sensorless / Belief State Tracking:** Vận hành bộ não cho Stalker `👻` (Agent mù). Duy trì và cập nhật tập Niềm tin (Belief State) qua phương trình Predict + Observe dựa trên cảm biến ngửi mùi bán kính 3 ô.

  <video src="https://github.com/user-attachments/assets/1dbfc4da-85b5-47b6-97fa-5b45eeab398f" controls muted width="700"></video>

* **8. AND-OR Graph Search:** Tìm kiếm kế hoạch dự phòng (Contingency Plan) trong môi trường không tất định (trượt ngã trên ô Băng 50%). Trực quan hóa bằng Cây quyết định tương tác highlight ô mê cung.

  <video src="https://github.com/user-attachments/assets/24e65d52-baaa-4845-9fb5-ad33639ff08a" controls muted width="700"></video>

---

### Nhóm 5: Bài toán thỏa mãn ràng buộc (CSP)

* **9. Min-Conflicts (Local Search CSP):** Vận hành khi **Khởi tạo Game mới**. Trực quan hóa từng bước gán màu ngẫu nhiên ban đầu cho 6 vùng an toàn và tự động sửa đổi các mâu thuẫn màu giáp ranh.

  <video src="https://github.com/user-attachments/assets/e8718948-8dda-4d34-a42d-8277f43e4be1" controls muted width="700"></video>

* **10. Backtracking Search:** Vận hành khi **Mất 1 Mạng sống**. Chạy đệ quy quay lui (kết hợp Heuristic MRV) để tái cấu trúc lại màu sắc các vùng an toàn từ đầu, đồng thời biến phân vùng ngay tại vị trí Robot đang đứng thành Vùng Lục 🟢 an toàn.

  <video src="https://github.com/user-attachments/assets/76cc8b3f-3ab4-4f0c-bbf6-935c0a5af352" controls muted width="700"></video>

---

### Nhóm 6: Tìm kiếm đối kháng (Adversarial Search)

* **11. Minimax:** Vận hành bộ não AI cho đối thủ trong màn đấu trí Caro 3x3 khi đụng độ Bảo vệ Greedy (duyệt toàn bộ $9!$ trạng thái).

  <video src="https://github.com/user-attachments/assets/9fc4b2f4-8f77-4144-a0eb-42626478c715" controls muted width="700"></video>

* **12. Alpha-Beta Pruning:** Vận hành trí tuệ nhân tạo mức độ khó cao nhất (cắt tỉa nhánh thừa $\alpha,\beta$) khi đụng độ Bảo vệ A* và Stalker.

  <video src="https://github.com/user-attachments/assets/8910bcbd-a2d6-4322-a28c-4a803932cad7" controls muted width="700"></video>

