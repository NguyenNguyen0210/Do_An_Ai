# BÁO CÁO CUỐI KỲ MÔN TRÍ TUỆ NHÂN TẠO
**Tên đồ án:** AI Maze Quest – Hệ thống ứng dụng 6 nhóm thuật toán AI kinh điển

---

## I. BÀI TOÁN ĐẶT RA

### 1. Bài toán gì?
Đồ án xây dựng một trò chơi nhập vai **"Mê cung giải cứu đa tác nhân" (AI Maze Quest)**. Trong đó, người chơi sẽ điều khiển một Robot cứu hộ (🤖) di chuyển qua các địa hình phức tạp (bùn lầy tốn chi phí, băng trơn ngẫu nhiên) để giải cứu 3 nạn nhân (🤕) và thoát khỏi mê cung qua Cửa thoát hiểm (🚪). Cùng lúc đó, hệ thống trò chơi ứng dụng đồng bộ trọn vẹn **12 thuật toán Trí tuệ Nhân tạo (thuộc 6 nhóm chủ đề)** để vận hành thế giới trò chơi và điều khiển các Lính gác (Guards) săn lùng Robot một cách thông minh nhất.

### 2. Mô hình PEAS của bài toán
Để thiết kế tác nhân AI (Agent), bài toán được mô hình hóa theo cấu trúc PEAS chuẩn xác như sau:
*   **P (Performance measure - Hiệu suất):** Tối thiểu hóa thời gian và số bước di chuyển, bảo toàn mạng sống (3 mạng), giải cứu đủ 3 nạn nhân và thoát khỏi mê cung qua ô Cửa ra `🚪`.
*   **E (Environment - Môi trường):** Môi trường 2D dạng lưới (Grid) 15x19 không gian rời rạc. Bao gồm tường vây quanh, địa hình tốn chi phí (Bùn 🐾), địa hình không tất định (Băng ❄️), các phân vùng an toàn/báo động chiến thuật (CSP Security Zones), và tập "Niềm tin" quan sát một phần đối với lính gác tàng hình Stalker. Trạng thái môi trường thay đổi theo từng lượt (Turn-based).
*   **A (Actuators - Bộ truyền động):** 4 hướng di chuyển cơ bản trên mê cung: Lên, Xuống, Trái, Phải. Các hành động chọn nước cờ (đặt X/O) trong minigame đối kháng Tic-Tac-Toe 3x3.
*   **S (Sensors - Cảm biến):** Lấy thông tin lưới mê cung, hàm tính khoảng cách Manhattan/Euclidean, và hệ thống Cảm biến thính giác/khứu giác ngửi mùi trong bán kính 3 ô của Stalker.

---

## II. QUY LUẬT VÀ CÁCH CHƠI CHI TIẾT (GAMEPLAY & RULES)

### 1. Chúng ta là ai? (Nhân vật đại diện)
Người chơi nhập vai **Robot Cứu Hộ 🤖 (Rescue Robot R)** thông minh, được cử vào mê cung nguy hiểm bị bao vây bởi các lính gác tuần tra tự động. Nhiệm vụ của Robot là di chuyển chiến thuật để tìm kiếm, cứu sống các nạn nhân bị mắc kẹt và tìm đường thoát hiểm an toàn.

### 2. Mục tiêu trò chơi & Cách chiến thắng
* **Giải cứu Nạn nhân:** Người chơi điều khiển Robot di chuyển lần lượt tới vị trí của **3 Nạn nhân 🤕** (được ký hiệu và đánh số từ 1 đến 3) để tích lũy giải cứu.
* **Thoát khỏi mê cung:** Sau khi cứu đủ 3 nạn nhân, Robot cần di chuyển đến vị trí ô **Cửa thoát hiểm 🚪 (Exit E)** tại góc dưới mê cung để hoàn thành màn chơi và giành chiến thắng.
* **Quản lý Mạng sống:** Robot khởi đầu với **3 Mạng sống (`lives = 3`)**. Nếu bị mất hết mạng sống khi thua đấu trí với lính gác, trò chơi kết thúc (Game Over).

### 3. Hệ thống Kẻ thù & Bảo vệ (Guards & Stalker)
Thế giới mê cung được tuần tra bởi 3 loại lính gác AI với khả năng và mức độ nguy hiểm khác nhau:
* 🔴 **Bảo vệ A* 👮‍♂️ (Viền đỏ Glow):** Lính gác di chuyển dựa trên thuật toán A* Search, tính toán chính xác chi phí địa hình và chủ động đi vòng né vũng bùn để đuổi bắt Robot tối ưu nhất.
* 🟠 **Bảo vệ Greedy 👮‍♂️ (Viền cam Glow):** Lính gác hung hãn di chuyển dựa trên thuật toán Greedy Best-First Search, nhắm thẳng tới tọa độ Robot theo đường chim bay.
* 🟣 **Stalker 👻 (Viền tím Glow):** Kẻ đi săn tàng hình (Agent mù), di chuyển và săn lùng Robot dựa trên cảm biến ngửi mùi/tiếng bước chân trong bán kính 3 ô (Belief State Tracking).

### 4. Hệ thống Địa hình Mê cung (Terrains & Costs)
* 🧱 **Tường vây 3D Firewall `#`:** Chướng ngại vật cố định, Robot và Lính gác không thể đi xuyên qua.
* 🐾 **Bùn lầy Mud (Màu nâu `#5D4037`):** Địa hình tốn chi phí. Mỗi lần Robot bước vào ô Bùn sẽ tiêu tốn **3 bước chi phí** ($g(n)=3$), khiến Robot bị làm chậm và lính gác dễ vây bắt.
* ❄️ **Vũng băng trơn Ice (Gradient xanh lam):** Địa hình không tất định. Khi Robot bước vào ô Băng sẽ có **50% rủi ro ngẫu nhiên bị trượt chân** dạt sang ô lân cận.

### 5. Cơ chế Phân vùng Chiến thuật CSP (Security Zones)
Bản đồ được chia thành 6 phân vùng an toàn/báo động được tô màu bằng thuật toán CSP:
* 🔴 **Vùng Đỏ (Báo động):** Lính gác di chuyển với tốc độ bình thường (1 ô sau mỗi lượt di chuyển của người chơi).
* 🔵 **Vùng Lam (Gây nhiễu):** Hệ thống điều khiển lính gác bị gây nhiễu, lính gác bị làm chậm (chỉ di chuyển 1 ô sau mỗi 2 bước di chuyển của người chơi).
* 🟢 **Vùng Lục (An toàn):** Robot hoàn toàn miễn nhiễm bị lính gác bắt. Mỗi khi Robot bị thua đấu trí mất 1 mạng, thuật toán Backtracking CSP sẽ tự động tái cấu trúc và đưa Vùng Lục về ngay vị trí ô Robot đang đứng để bảo vệ người chơi.

### 6. Màn Đấu Trí Minigame Caro 3x3 khi bị bắt (Duel System)
Khi lính gác di chuyển chạm vào ô của Robot (ngoại trừ khi Robot đang đứng ở Vùng Lục an toàn), một màn **Đấu Trí đối kháng Caro 3x3 (Tic-Tac-Toe)** sẽ xuất hiện:
* Người chơi thi đấu trực tiếp với bộ não AI (sử dụng thuật toán Minimax hoặc Alpha-Beta Pruning).
* **Nếu Thắng hoặc Hòa:** Robot dùng trí tuệ hạ gục bảo vệ vĩnh viễn và tiếp tục hành trình.
* **Nếu Thua:** Robot bị mất 1 mạng sống và Vùng An Toàn 🟢 được kích hoạt ngay dưới chân để bảo vệ người chơi.

---

## III. THUẬT TOÁN ÁP DỤNG
*Ghi chú: Dưới đây đại diện các thuật toán cốt lõi thuộc 6 nhóm chủ đề được ứng dụng trực tiếp trong game.*

### 1. Nhóm Thuật toán Tìm kiếm mù thông tin (Đại diện: BFS - Breadth First Search)
*   **Trạng thái bắt đầu:** Vị trí Lối ra (Exit `🚪`).
*   **Trạng thái mục tiêu:** Toàn bộ các ô trống có thể đi được trên bản đồ.
*   **Các bước tìm ra solution:** 
    1. Khởi tạo một hàng đợi (Queue) chứa điểm xuất phát `🚪` với chi phí `0`.
    2. Lan tỏa (Flood-fill) theo chiều rộng ra 4 hướng lân cận.
    3. Ở mỗi hướng, kiểm tra nếu không phải tường và chưa được duyệt, cập nhật chi phí `bước đi + 1` và đưa vào Queue.
    4. Lặp lại cho đến khi Queue rỗng. Kết quả thu được là một Trường Khoảng cách (Distance Field) cung cấp khoảng cách ngắn nhất chính xác từ mọi điểm về Lối ra.

### 2. Nhóm Thuật toán Tìm kiếm có thông tin (Đại diện: A* Search)
*   **Trạng thái bắt đầu:** Tọa độ hiện tại của Lính gác `A*`.
*   **Trạng thái mục tiêu:** Tọa độ hiện tại của Robot (Người chơi).
*   **Các bước tìm ra solution:**
    1. Sử dụng hàm đánh giá $f(n) = g(n) + h(n)$ (với $g(n)$ là chi phí thực tế đi qua vũng bùn 🐾 có trọng số = 3, $h(n)$ là khoảng cách Manhattan tới Robot).
    2. Đưa Trạng thái bắt đầu vào Hàng đợi ưu tiên (Priority Queue).
    3. Rút Node có $f(n)$ nhỏ nhất ra khỏi Queue. Sinh các ô lân cận và tính lại $f(n)$.
    4. Khi chạm tọa độ Robot, truy xuất ngược (backtrack) để tạo ra lộ trình truy đuổi thông minh biết chủ động đi vòng né vũng bùn.

### 3. Nhóm Thuật toán Tìm kiếm cục bộ (Đại diện: Steepest-Ascent Hill Climbing)
*   **Trạng thái bắt đầu:** Vị trí hiện tại của Robot và tập các nạn nhân chưa cứu.
*   **Trạng thái mục tiêu:** Hoán vị lộ trình giải cứu có tổng chi phí nhỏ nhất.
*   **Các bước tìm ra solution:**
    1. Duyệt qua tất cả các trạng thái lân cận bằng cách đổi chỗ (swap) thứ tự giải cứu các nạn nhân.
    2. Tính toán tổng khoảng cách thực tế giữa các mốc bằng A* Search.
    3. Chọn ra trạng thái hàng xóm có độ dốc cải thiện tốt nhất (Steepest-Ascent).
    4. Trả về lộ trình tối ưu nhất để vẽ bộ mũi tên chỉ đường Neon Sci-Fi Cyan (`▲▼◄►`).

### 4. Nhóm Môi trường Phức tạp (Đại diện: AND-OR Graph Search)
*   **Trạng thái bắt đầu:** Tọa độ Robot đang đứng trước các vũng Băng.
*   **Trạng thái mục tiêu:** Tọa độ Nạn nhân hoặc Lối ra cần tới.
*   **Các bước tìm ra solution:**
    1. Nút OR đại diện cho quyết định chọn hướng di chuyển của Robot.
    2. Nút AND đại diện cho môi trường không tất định: NẾU di chuyển thành công thì sao, NẾU bị trượt chân ngẫu nhiên 50% trên ô Băng `❄️` sang ô lân cận thì sao.
    3. Gọi đệ quy bao quát toàn bộ các nhánh rủi ro. Cây kết quả được hiển thị trên cửa sổ tương tác, nhấp chọn nút dòng trên cây sẽ highlight ô tương ứng trên mê cung (`#FF00FF` + `🎯`).

### 5. Nhóm Thỏa mãn ràng buộc CSP (Đại diện: Min-Conflicts & Backtracking Search)
*   **Trạng thái bắt đầu:** 6 phân vùng an toàn chiến thuật trên bản đồ (`Z0` - `Z5`).
*   **Trạng thái mục tiêu:** Phân bổ màu sắc (Đỏ, Lục, Lam) cho 6 vùng sao cho không có 2 vùng kề nhau trùng màu.
*   **Các bước tìm ra solution:**
    1. **Khi khởi tạo game mới (Min-Conflicts):** Gán màu ngẫu nhiên cho 6 vùng, sau đó thuật toán Min-Conflicts tự động duyệt và sửa đổi các mâu thuẫn màu giáp ranh từng bước một trực quan.
    2. **Khi mất 1 mạng sống (Backtracking Search):** Thuật toán đệ quy quay lui kết hợp Heuristic MRV sẽ tính toán tái cấu trúc lại toàn bộ mảng màu phân vùng an toàn từ đầu.

### 6. Nhóm Tìm kiếm Đối kháng (Đại diện: Alpha-Beta Pruning)
*   **Trạng thái bắt đầu:** Bảng caro Tic-Tac-Toe 3x3 khi người chơi bị bảo vệ bắt.
*   **Trạng thái mục tiêu:** AI giành chiến thắng hoặc hòa cờ.
*   **Các bước tìm ra solution:**
    1. Giả lập cây trò chơi với hai người chơi MAX (AI) và MIN (Người chơi).
    2. Duy trì hai giá trị cắt tỉa $\alpha$ (nước đi tốt nhất của MAX) và $\beta$ (nước đi tốt nhất của MIN).
    3. Trong quá trình duyệt cây, nếu phát hiện nhánh MIN có giá trị $\le \alpha$, thực hiện cắt tỉa (Prune) lập tức để tiết kiệm tài nguyên và nâng cao tốc độ phản hồi.

---

## IV. THỰC NGHIỆM VÀ KẾT QUẢ (12 THUẬT TOÁN)

### 1. Nhóm Thuật toán Tìm kiếm mù thông tin (Uninformed Search)
*   **1. Thuật toán DFS (Depth-First Search):**
    *   *Kết quả thực nghiệm:* Vận hành tiến trình **Mô phỏng đục tường 4 giai đoạn** khi bắt đầu game. Thuật toán Recursive Backtracker đục từng ô tường thô trên nền tối neutral, hiển thị con trỏ tia sét `⚡` lướt mượt mà theo thời gian thực.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP MÔ PHỎNG ĐỤC TƯỜNG DFS TIA SẾT TẠI ĐÂY]`
*   **2. Thuật toán BFS (Breadth-First Search):**
    *   *Kết quả thực nghiệm:* Lan tỏa theo chiều rộng tính toán Trường khoảng cách từ Lối ra `🚪` tới mọi ô trống. Thẻ trạng thái cập nhật số bước BFS ngắn nhất theo thời gian thực khi Robot bước đi.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP THẺ KHOẢNG CÁCH BFS LỐI RA TẠI ĐÂY]`

### 2. Nhóm Thuật toán Tìm kiếm có thông tin (Informed Search)
*   **3. Thuật toán A* Search:**
    *   *Kết quả thực nghiệm:* Điều khiển Bảo vệ A* (`👮‍♂️` viền đỏ). Nhờ hàm chi phí $g(n)$, Bảo vệ A* thông minh nhận biết ô Bùn `🐾` (chi phí 3) và chủ động đi vòng qua đường gạch sạch sẽ để truy đuổi Robot tối ưu nhất.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP BẢO VỆ A* ĐI VÒNG NÉ BÙN TẠI ĐÂY]`
*   **4. Thuật toán Greedy Best-First Search:**
    *   *Kết quả thực nghiệm:* Điều khiển Bảo vệ Greedy (`👮‍♂️` viền cam). Chạy siêu nhanh dựa trên khoảng cách Manhattan $h(n)$, nhắm thẳng hướng Robot nhưng dễ bị vướng tường hoặc lội qua vũng bùn.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP BẢO VỆ GREEDY TRUY ĐUỔI TẠI ĐÂY]`

### 3. Nhóm Thuật toán Tìm kiếm cục bộ (Local Search)
*   **5. Thuật toán Simple Hill Climbing:**
    *   *Kết quả thực nghiệm:* Vận hành tính năng "Đi Tự Động". Thuật toán chọn ngay nước đi tốt hơn đầu tiên để điều khiển Robot di chuyển mượt mà từng bước.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP ĐI TỰ ĐỘNG SIMPLE HC TẠI ĐÂY]`
*   **6. Thuật toán Steepest-Ascent Hill Climbing:**
    *   *Kết quả thực nghiệm:* Vận hành tính năng "Bật Chỉ Đường". Duyệt toàn bộ hàng xóm để chọn hướng dốc nhất, vẽ ra chuỗi mũi tên Neon Sci-Fi Cyan (`▲▼◄►`) dẫn đường tối ưu qua các nạn nhân.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP LỘ TRÌNH MŨI TÊN NEON CYAN TẠI ĐÂY]`

### 4. Nhóm Môi trường Phức tạp (Complex Environments)
*   **7. Thuật toán Belief State Tracking (Partially Observable):**
    *   *Kết quả thực nghiệm:* Vận hành bộ não cho Stalker `👻` (Agent mù). Duy trì tập Niềm tin ngầm ở backend. Cảm biến ngửi mùi bán kính 3 ô thu hẹp mảng nghi vấn và phát cảnh báo lên nhật ký hệ thống.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP STALKER VÀ LOG CẢNH BÁO MÙI TẠI ĐÂY]`
*   **8. Thuật toán AND-OR Graph Search (Non-deterministic):**
    *   *Kết quả thực nghiệm:* Xây dựng Cây kế hoạch dự phòng vượt địa hình Băng trơn. Cửa sổ hiển thị trực quan cây quyết định, hỗ trợ tương tác nhấp dòng để khoanh vùng highlight ô tương ứng trên mê cung (`#FF00FF` + `🎯`).
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP CỬA SỔ CÂY AND-OR VÀ HIGHLIGHT LƯỚI TẠI ĐÂY]`

### 5. Nhóm Thỏa mãn ràng buộc CSP (Constraint Satisfaction Problems)
*   **9. Thuật toán Min-Conflicts (Local Search CSP):**
    *   *Kết quả thực nghiệm:* Vận hành khi **Khởi tạo Game mới**. Trực quan hóa chậm rãi bước 1 (gán màu ngẫu nhiên cho 6 vùng chiến thuật Zone 0 - Zone 5) và các bước tiếp theo (thuật toán tự động sửa đổi xung đột màu cục bộ để **đi tới một trạng thái thỏa mãn hoàn chỉnh không có 2 vùng giáp ranh nào trùng màu, từ đó thiết lập trận đồ chiến thuật chuẩn xác gồm Vùng Lục 🟢 an toàn, Vùng Lam 🔵 gây nhiễu và Vùng Đỏ 🔴 báo động**).
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP TRỰC QUAN TÔ MÀU MIN-CONFLICTS TẠI ĐÂY]`
*   **10. Thuật toán Backtracking Search (kết hợp MRV):**
    *   *Kết quả thực nghiệm:* Vận hành khi người chơi thua đấu trí và **Mất 1 Mạng sống**. Thuật toán ứng dụng cơ chế đệ quy quay lui (kết hợp Heuristic MRV) để **tái cấu trúc lại mảng màu của 6 phân vùng an toàn, đồng thời cố định phân vùng ngay tại tọa độ Robot đang đứng thành Vùng Lục 🟢 an toàn, giúp bảo vệ người chơi miễn nhiễm khỏi nguy cơ tiếp tục bị lính gác vây bắt ngay lập tức**.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP RE-COLOR BẢN ĐỒ KHI MẤT MẠNG TẠI ĐÂY]`

### 6. Nhóm Tìm kiếm Đối kháng (Adversarial Search)
*   **11. Thuật toán Minimax:**
    *   *Kết quả thực nghiệm:* Vận hành bộ não AI Tic-Tac-Toe 3x3 khi đụng độ Bảo vệ Greedy. Duyệt toàn bộ $9!$ trạng thái, đánh chặn chính xác nước đi của người chơi.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP MINIGAME CARO MINIMAX TẠI ĐÂY]`
*   **12. Thuật toán Alpha-Beta Pruning:**
    *   *Kết quả thực nghiệm:* Vận hành bộ não AI Tic-Tac-Toe 3x3 độ khó cao khi đụng độ Bảo vệ A* và Stalker. Cắt tỉa các nhánh thừa $\alpha, \beta$ giúp AI phản hồi tức thì.
    > `[CHÈN ẢNH ĐỘNG/ẢNH CHỤP MINIGAME CARO ALPHA-BETA TẠI ĐÂY]`

**🔗 GITHUB REPOSITORY CỦA NHÓM:** `[Dán đường link Github source code tại đây]`

---

## V. ĐÁNH GIÁ VÀ THẢO LUẬN

### 1. Bảng so sánh các thuật toán (Dựa trên thông số vận hành của Game)

| Nhóm | Thuật toán 1 | Thuật toán 2 | Kết luận chênh lệch |
| :--- | :--- | :--- | :--- |
| **Informed Search** | **A\* Search:** Duyệt node kỹ lưỡng, luôn tìm được đường ngắn nhất né vũng bùn. | **Greedy BFS:** Tốc độ thực thi siêu nhanh, nhưng dễ lội qua bùn hoặc kẹt tường. | A* thông minh hơn trong môi trường địa hình phức tạp, Greedy phù hợp di chuyển tốc độ. |
| **Local Search** | **Simple HC:** Duyệt hàng xóm lần lượt, thấy tốt hơn là đi ngay để di chuyển tự động nhanh chóng. | **Steepest-Ascent HC:** Duyệt tất cả hàng xóm, chọn hướng dốc nhất để vẽ lộ trình GPS tối ưu tuyệt đối. | Simple HC giúp tính nhanh bước đi lẻ, Steepest-Ascent HC vẽ đường gợi ý tổng thể hoàn hảo. |
| **CSP** | **Min-Conflicts:** Khởi tạo ngẫu nhiên và sửa đổi cục bộ từng bước linh hoạt khi tạo game. | **Backtracking Search:** Tìm kiếm đệ quy triệt để, tái cấu trúc toàn bộ không gian màu khi mất mạng. | Min-Conflicts tạo hiệu ứng trực quan sinh động, Backtracking đảm bảo bài toán luôn có lời giải triệt để. |
| **Adversarial** | **Minimax:** Duyệt toàn bộ $9!$ trạng thái cây trò chơi. | **Alpha-Beta Pruning:** Số Node duyệt giảm rõ rệt nhờ kỹ thuật cắt tỉa $\alpha, \beta$. | Alpha-Beta Pruning đem lại hiệu năng phản hồi vượt trội cho minigame real-time. |

### 2. Ý kiến đánh giá của nhóm
Thông qua việc lập trình một dự án tích hợp đủ 6 nhóm môi trường AI, nhóm nhận thấy các thuật toán Trí tuệ Nhân tạo kết hợp đồng bộ đã đem lại "trí thông minh sinh động" cho toàn bộ trò chơi:
- Thuật toán **DFS** và **BFS** tạo nên một bản đồ sống động, liên thông tuyệt đối.
- Thuật toán **A\*** và **Greedy** biến các lính gác thành những đối thủ săn lùng thực thụ.
- Sự kết hợp **Min-Conflicts** và **Backtracking** làm cho hệ thống vùng chiến thuật CSP thay đổi biến ảo, còn **AND-OR Graph Search** đem lại khả năng hoạch định dự phòng rủi ro chính xác.

---

## VI. KẾT LUẬN
Đồ án "AI Maze Quest" đã hoàn thiện 100% tất cả các mục tiêu đề ra. Bằng việc tự xây dựng toàn bộ thuật toán và giao diện đồ họa PyQt5, nhóm đã nắm vững kiến trúc tác nhân AI, nguyên lý đệ quy, các hàm Heuristic đánh giá và cách tích hợp AI vào vòng lặp trò chơi (Game Loop) thực tế.

**TÀI LIỆU THAM KHẢO**
1. Stuart Russell and Peter Norvig, *Artificial Intelligence: A Modern Approach (4th Edition)*, Pearson.
2. Tài liệu bài giảng môn Trí tuệ Nhân tạo của Giảng viên.
3. Tài liệu Documentation thư viện giao diện đồ họa PyQt5.
