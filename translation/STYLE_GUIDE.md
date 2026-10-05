# Quy tắc dịch Torchlight II — kiểu "mix Anh–Việt"

Mục tiêu: người chơi hiểu được **hội thoại** và **phần giải thích** (mô tả kỹ năng, vật phẩm, hiệu ứng, hướng dẫn, giao diện),
nhưng **mọi tên gọi vẫn là tiếng Anh**, để khi lên diễn đàn quốc tế hay chơi cùng người khác, tên chiêu thức, vật phẩm và quái
vẫn khớp với bản gốc.

## 1. Luôn GIỮ NGUYÊN tiếng Anh

1. **Tên riêng**: tên kỹ năng/chiêu thức, vật phẩm (kể cả Unique/Legendary/Set), quái, boss, NPC, pet, địa danh/khu vực/
   dungeon, tên nhiệm vụ, tên bộ trang bị, phe phái, thần linh, danh hiệu, sự kiện.
   Không chắc một cụm có phải tên không → tra `translation/names_keep_english.txt` (danh sách tên lấy từ dữ liệu game).
   Tên thường viết hoa từng chữ (Title Case).
2. **Lớp nhân vật**: Berserker, Embermage, Engineer, Outlander.
3. **Chỉ số gốc**: Strength, Dexterity, Focus, Vitality.
4. **Hệ sát thương**: Physical, Fire, Ice, Electric, Poison, Elemental. Ví dụ: "sát thương Fire", "kháng Ice".
5. **Thuật ngữ game**: Mana, Charge (thanh Charge), Rage, Execute, Fumble, DPS, Fame, Ember, Gem, Socket, Pet, Boss, Champion, Hardcore,
   New Game Plus / NG+, Mapworks, Enchanter, Transmuter, Tome, Scroll, Potion.
   - Độ hiếm: Normal, Magic, Rare, Unique, Legendary, Set.
   - Loại vật phẩm: Sword, Axe, Mace, Greatsword, Greataxe, Greathammer, Polearm, Staff, Wand, Pistol, Rifle, Shotgonne,
     Cannon, Bow, Crossbow, Claw, Shield, Helmet, Chest Armor, Shoulder Armor, Gloves, Belt, Pants, Boots, Ring, Amulet,
     Collar, Studs, Spell…
   - Độ khó: Casual, Normal, Veteran, Elite.
   - Thuật ngữ đồ họa/kỹ thuật: V-Sync, Anti-Aliasing, Bloom, FPS, DirectX, OpenGL…
6. **Lệnh chat** (bắt đầu bằng `/`), tên phím (Shift, Ctrl, Alt, Tab, Space, F1…), tên file, URL.

## 2. Thuật ngữ DỊCH (dùng thống nhất)

| Tiếng Anh | Tiếng Việt |
|---|---|
| damage | sát thương |
| health (chỉ số, máu) | máu |
| armor (chỉ số) | giáp |
| critical hit / critical chance | đòn chí mạng / tỉ lệ chí mạng |
| dodge / block | né tránh / đỡ đòn |
| attack speed / cast speed / movement speed | tốc độ đánh / tốc độ thi triển / tốc độ di chuyển |
| knockback | đẩy lùi |
| stun / slow / freeze | làm choáng / làm chậm / đóng băng |
| burn / shock / poisoned | thiêu đốt / sốc điện / trúng độc |
| immobilize / fear, terror / charm / blind | bất động / hoảng sợ / mê hoặc / làm mù |
| resistance / armor penetration | kháng / xuyên giáp |
| life steal / mana steal | hút máu / hút mana |
| heal / regenerate, regeneration | hồi máu / hồi phục |
| level | cấp |
| experience | kinh nghiệm |
| gold | vàng |
| quest | nhiệm vụ |
| skill / passive skill | kỹ năng / kỹ năng bị động |
| skill point / stat point / attribute | điểm kỹ năng / điểm thuộc tính / thuộc tính |
| cooldown | thời gian hồi |
| duration | thời gian hiệu lực |
| second(s) / minute(s) | giây / phút |
| chance | tỉ lệ (hoặc "có x% cơ hội") |
| enemy, foe / monster / ally | kẻ địch / quái / đồng minh |
| minion / summon | tay sai / triệu hồi |
| weapon / melee / ranged | vũ khí / cận chiến / tầm xa |
| projectile, missile | đạn |
| area / radius / target | khu vực / bán kính / mục tiêu |
| cast (spell) | thi triển |
| town / portal / waypoint / dungeon | thị trấn / cổng dịch chuyển / điểm dịch chuyển / hầm ngục |
| inventory / stash / shared stash | hành trang / rương đồ / rương chung |
| equipment, gear | trang bị |
| identify / unidentified | giám định / chưa giám định |
| merchant, vendor / buy / sell | thương nhân / mua / bán |
| respec | tẩy điểm |
| aura | hào quang |
| buff / debuff | hiệu ứng có lợi / hiệu ứng bất lợi |

## 3. Định dạng kỹ thuật — BẮT BUỘC giữ đúng

- Giữ **chính xác** mọi token, không dịch, không đổi chính tả, không thêm hay bớt:
  `[VALUE]`, `[VALUE2]`, `[VALUE3AND4]`, `[DURATION]`, `[ITEM]`, `[NAME]`, `[DMGTYPE]`, `[PLAYERNAME]`, `[GOLD]`,
  `[COMMAND_PARAM]`, `[[KB:...]]`, `<STAT1>`, `<stat:...>`, `<playername>`… (mọi thứ trong `[...]` hoặc `<...>`).
  Được **đổi vị trí** token cho đúng ngữ pháp tiếng Việt.
- Mã màu: `|cFFRRGGBB` mở màu, `|u` đóng màu. Giữ nguyên và bao đúng phần chữ tương ứng.
- `\n` trong dữ liệu là **hai ký tự** (dấu gạch chéo + n) để xuống dòng. Giữ đúng số lượng, kể cả khoảng trắng thụt đầu
  dòng phía sau.
- Giữ nguyên khoảng trắng ở **đầu/cuối** chuỗi, dấu `+`/`-` và số liệu. Không đổi con số.
- Dùng tiếng Việt Unicode dựng sẵn (NFC). Không dùng emoji hay ký tự lạ.

## 4. Văn phong

- Tự nhiên, gọn, dễ hiểu. Giao diện có chỗ hẹp: nhãn nút/menu cố gắng **không dài hơn ~130%** bản tiếng Anh.
- Viết hoa kiểu câu (chỉ chữ đầu), trừ tên riêng tiếng Anh giữ nguyên cách viết hoa.
- Hội thoại: NPC thân thiện xưng "tôi", gọi người chơi là "bạn". Kẻ thù, boss, thần linh, sinh vật cổ xưa, kẻ kiêu ngạo:
  xưng "ta", gọi "ngươi". Giữ đúng giọng điệu (hài hước, bí ẩn, đe dọa…).
- Mô tả vật phẩm (flavor text): dịch sát ý, giữ chất văn; chơi chữ khó dịch thì dịch ý.
- Không thêm thông tin, không bỏ ý.

## 5. Ví dụ

| English | Tiếng Việt |
|---|---|
| `+[VALUE]% Fire Damage` | `+[VALUE]% sát thương Fire` |
| `+[VALUE] Strength` | `+[VALUE] Strength` |
| `[VALUE]% chance to Stun for 2 seconds` | `[VALUE]% tỉ lệ làm choáng trong 2 giây` |
| `+[VALUE] Melee weapon damage bonus for [DURATION]` | `+[VALUE] sát thương vũ khí cận chiến trong [DURATION]` |
| `Requires Level [VALUE]` | `Yêu cầu cấp [VALUE]` |
| `Entered\nSlavers' Camp` | `Đã vào\nSlavers' Camp` |
| `To The Temple Steppes` | `Đến The Temple Steppes` |
| `Resurrect here, but lose [GOLD] Gold.` | `Hồi sinh tại chỗ, nhưng mất [GOLD] vàng.` |
| `\|cFFF5DB94[PLAYERNAME] waves.\|u` | `\|cFFF5DB94[PLAYERNAME] vẫy tay.\|u` |
| `The Glaive rebounds 2 times` | `Glaive nảy bật 2 lần` |
| `Welcome to Fort Cardinal, friend.` | `Chào mừng đến Fort Cardinal, bạn của tôi.` |

## 6. Chuỗi "decide" (không rõ ngữ cảnh)

Nếu chuỗi là **tên riêng** (khu vực, vật phẩm, quái, NPC, kỹ năng, nhiệm vụ…), là thuật ngữ trong mục 1, hoặc là chuỗi
kỹ thuật/debug không dành cho người chơi → **trả lại y nguyên** bản tiếng Anh. Nếu không → dịch như bình thường.
