# 《潮线之上（Last Landfall）》开场 CG v2 总方案与全分镜提示词

> **审核修正说明（针对 v1 试点问题）：**
> 1. **美术风格重构**：v1 使用了灰暗半写实概念图提示词，既不像写实摄影也不像精致动漫。本方案统一对齐项目参考图 [OpeningComicIntro.png](../OpeningComicIntro.png) 的**高水准剧场版 2D 动画电影风**（清晰线条、戏剧光影、通透大气透视与电影色彩脚本）。生成关键帧时，在 ChatGPT 新对话第一轮直接上传 `OpeningComicIntro.png` 作为官方画风锚点。
> 2. **现实逻辑修正**：
>    - 天文台（S01）是**隔热玻璃观测控制室**，工作人员穿普通御寒毛衣/夹克、使用真实的暗色星图轨迹屏（**绝不在天文台里穿救生衣**）。
>    - 主角（30 岁左右短黑发女救援队员：褪色锈橙防水外套 + 暗红救生衣 + 左臂无文字白色三角布章）仅从 **S06 沿海救援站与出海救援** 阶段开始登场，服装与职业场景完全合理。
> 3. **叙事结构（严格遵循原反转剧本）**：
>    - **第一幕（误判与欢呼）**：天文台发现稀疏碎片（S01）→ 防御系统成功拦截、城市广场人群欢呼以为靠自己化解了危机（S02）。
>    - **第二幕（太阳盲区突袭与海啸）**：主碎片流从太阳眩光盲区出现（S03）→ 密集撞击外海（S04）→ 巨型海啸吞没沿海城市（S05）。
>    - **第三幕（断网、救援与海面缓涨）**：电网卫星失效，救援站短波捕获信号（S06）→ 风浪中首次小艇救援（S07）→ 多年降雨与冰屑融水使海平面逐年缓慢上涨（S08）。
>    - **第四幕（最后的高地）**：主角带两名船员驾驶橙白救援艇绕过沉船信号点驶向多台地荒岛（S09）→ 镜头拉升俯瞰高地主岛、晨光破云、留白淡入游戏（S10）。
> 4. **零变形首尾帧工作流**：每个镜头严格待在**同一物理空间**内，禁止跨空间融化；且在 ChatGPT 中采用 **“先画首帧 A → 基于 A 微调推拉/动作生成尾帧 B”**，保证首尾帧像素级对齐。

---

## 一、 时长与积分预算（适配 Google Flow `Omni 1.2 Flash`）

* 实测限制：Flow 的 `Omni 1.2 Flash` 在开启首尾帧（`帧`）时，最高支持 **10 秒**（14–15 秒不支持图片素材）。
* **总计 10 个镜头，总时长 92 秒（1 分 32 秒）**：
  * 节奏快的动作/情绪/转折镜用 **8 秒**（24 积分/段 × 4 段 = 96 积分）
  * 需要压迫感、尺度感、时间流逝与落版呼吸感的镜用 **10 秒**（30 积分/段 × 6 段 = 180 积分）
  * **预计总消耗：276 积分**（按当前剩余 **330 积分** 计算，还可余 **54 积分** 用于 1–2 次重抽）。

| 镜号 | 时长 | 积分 | 剧本段落 | 核心空间 | 运镜方向 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **S01** | 8s | 24 | 天文台发现零散先导碎片 | 山顶天文台玻璃控制室 | 慢推近控制台与星图屏 |
| **S02** | 8s | 24 | 首次拦截成功、城市欢呼 | 晴朗沿海城市广场 | 从高空截击闪光下摇至欢呼人群 |
| **S03** | 10s | 30 | 反转：太阳眩光盲区现主群 | 近地太空轨道 | 从平静地球慢摇并拉向刺眼太阳眩光 |
| **S04** | 10s | 30 | 主碎片流坠入外海 | 沿海高地俯瞰外海与城市 | 固定/微震远景看流星群坠海起蒸汽墙 |
| **S05** | 10s | 30 | 海啸吞没沿海旧城 | 高地岩岸俯瞰低洼城区 | 慢后退略抬升，前景避难者与巨浪 |
| **S06** | 8s | 24 | 断网停电，短波响起求救声 | 沿海救援站内（夜） | 从熄灭屏幕窗景摇推至短波机与主角 |
| **S07** | 8s | 24 | 暴雨海面第一次小艇救援 | 暴雨暗青色近海 | 贴舷跟拍主角与队友拉起落水者 |
| **S08** | 10s | 30 | 多年海平面缓慢上涨 | 同一处沿海石堤与半沉街道 | 固定机位跨季延时，水位沿盐渍线爬升 |
| **S09** | 10s | 30 | 沿信号过沉船驶向高地岛 | 晨雾海峡（船尾跟拍） | 低位跟拍橙白救援艇绕过沉船望见岛屿 |
| **S10** | 10s | 30 | 俯瞰高地主岛、标题落版 | 高地岛上空 | 越过小艇拉升俯瞰岛屿与晨光，结尾定格 |

---

## 二、 ChatGPT 生图全套操作流程与提示词

### 第 0 步：先发画风与连续性总设定（上传 `OpeningComicIntro.png`）

在 ChatGPT 开启一个**全新对话**，上传 `Assets/LastLandfall/Art/Concepts/OpeningComicIntro.png`，发送以下开场定调指令：

```text
I am creating keyframe pairs (Start Frame & End Frame) for a 92-second anime-style opening cutscene for my survival game "Last Landfall".
Please match the exact art style of the uploaded reference image: crisp theatrical 2D anime movie illustration (clean ink outlines, rich painted backgrounds, dramatic cel-and-painterly lighting, realistic modern architectural & mechanical proportions, atmospheric clouds/water, zero muddy 3D look, zero readable text/letters/watermarks, 16:9 widescreen).

Recurring continuity anchors (only appear from S06 onward):
- Heroine: 30-year-old female maritime rescuer, short tousled black hair, wearing a faded rust-orange waterproof rescue jacket over a dark red life vest, dark work pants, and a plain blank white triangular patch on her left sleeve (NO text on patch).
- Rescue Boat: Practical weathered orange-and-white small coastal rescue boat with dark blue hull, boxy wheelhouse cabin, two round floodlights on the cabin roof, and an outboard engine at the stern.

Acknowledge these rules and wait for my S01_A prompt.
```

---

### S01｜天文台控制室发现零散先导碎片（8 秒）

* **审核要点**：玻璃暖室控制室与望远镜圆顶分离，人员穿普通羊毛衫/羽绒背心（**不穿救生衣**），屏幕显示简洁星图轨迹线与 4–5 个微小光点（无乱码文字）。
* **首帧 `S01_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S01_A in the exact theatrical 2D anime film style of the reference image.
  Scene: Inside a realistic modern mountain astronomical observatory control room at night, separated by a large angled glass window from the dark unheated telescope dome bay outside (where a sleek white optical telescope points through an open dome slit into cloudy midnight sky).
  Inside the dim control room, lit only by cool blue monitor light and low amber console indicator LEDs (no bright desk lamp glare), two tired astronomers in realistic winter knit sweaters and fleece vests sit at curved workstation desks. One older male astronomer holds a paper clipboard, while a young female analyst leans toward a wide dark-blue astrometric display showing an abstract starfield, Earth's curved orbital arc, and a faint dotted trajectory of 4 tiny icy specks approaching from afar. Clean ink lines, realistic modern equipment, NO life vests, NO readable text or numbers, 16:9.
  ```
* **尾帧 `S01_B`（同对话续画指令）**：
  ```text
  Generate S01_B by continuing directly from S01_A with the exact same room, characters, sweaters, telescope through the glass, and 2D anime film style.
  Camera moves 25% closer over the female analyst's shoulder toward the main astrometric display. The male astronomer leans in and points his pen calmly at the faint dotted arc of 4 tiny white specks on the screen. Their faces show serious professional focus, NOT panic. Eyes remain fixed on the monitor. No red alarm lights, no readable text or gibberish letters, 16:9.
  ```
* **Flow 视频提示词（`S01_A → S01_B`, Omni 1.2 Flash, 8s）**：
  ```text
  Theatrical 2D anime film animation in crisp painted cel style, cool midnight slate-blue and subdued amber console lighting. One smooth, steady 8-second dolly-in inside the enclosed glass-walled observatory control room toward the astrometric monitor. The female analyst leans slightly closer while the male astronomer raises his hand and calmly points a pen at the faint trajectory of 4 tiny specks on the screen; both keep their eyes locked strictly on the monitor with natural human expressions, never looking at the camera. Outside the dark glass window, clouds drift faintly past the open telescope dome slit. Subtle dust motes in monitor glow, smooth eased motion, no cuts, no camera shake, no red alarms, no readable text.
  ```

---

### S02｜首次拦截成功，城市广场欢呼（8 秒，人类以为靠自己解决危机）

* **审核要点**：直接呼应 `OpeningComicIntro.png` 第一格的晴朗海滨城市氛围；天空一次干净明亮的拦截闪光后，镜头微下摇，广场上仰望天空和户外大屏的人群松一口气、鼓掌欢呼，以为防空系统彻底化解了危机。
* **首帧 `S02_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S02_A in the exact theatrical 2D anime film style of the reference image (matching Panel 1's bright sunny coastal city mood).
  Scene: Bright clear blue daytime sky above a modern sunlit coastal city plaza beside the sea. High in the upper sky, a single brilliant golden-white interception flash shatters a small icy rock fragment into tiny harmless sparkling vapor trails, with a faint contrail curving up from the horizon. Below in the lower third of the frame, the top of a large outdoor plaza display screen mirrors the bright interception burst, and the tops of buildings and raised hands of a hopeful crowd are visible. Crisp sunlight, optimistic atmosphere, NO text, NO logos, 16:9.
  ```
* **尾帧 `S02_B`（同对话续画指令）**：
  ```text
  Generate S02_B by tilting the camera smoothly downward from S02_A in the exact same sunny coastal city plaza and 2D anime film style.
  Now the crowd and the large outdoor screen fill the midground and foreground: ordinary citizens in casual daytime jackets and office clothes look up with bright relieved smiles, cheering, clapping, and hugging gently; a father lifts a smiling child onto his shoulders, while the bright blue sky behind the tall waterfront buildings still holds a fading wispy white interception trail. Natural anatomy, clean faces, NO readable text or banners, 16:9.
  ```
* **Flow 视频提示词（`S02_A → S02_B`, Omni 1.2 Flash, 8s）**：
  ```text
  Theatrical 2D anime film animation, bright crisp daytime sunlight, vibrant cerulean sky and warm sunlit highlights. One continuous 8-second vertical camera tilt-down from the high blue sky to the coastal city plaza below. At the start, a distant pale-gold interception burst breaks a small icy rock into harmless drifting vapor wisps high in the sky; as the camera tilts smoothly downward past glistening glass towers and the large plaza screen, the sunlit crowd below erupts into relieved applause, smiles, and warm embraces, believing the danger is over. Gentle breeze rustling hair and jackets, smooth camera deceleration, no cuts, no readable text, no distortion on faces.
  ```

---

### S03｜反转：太阳眩光盲区涌出庞大主碎片流（10 秒）

* **审核要点**：高反差宇宙镜头——先看见晴朗无害的地球弧面，镜头摇向刺眼惨白的太阳眩光，逆光剪影中浮现铺天盖地、冰岩交错的主碎片流，彻底打破“危机已解”的错觉。
* **首帧 `S03_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S03_A in the exact theatrical 2D anime film style of the reference image.
  Scene: Serene outer space orbital view. Earth's peaceful, bright blue ocean curve and white cloud swirls fill the lower right half of the frame, with a blinding pale-white sun starting to peek from the upper-left dark void. Space looks calm and empty except for faint tiny glittering ice dust near the sun's glare. High-contrast cinematic lighting, crisp anime space painting, NO spaceships, NO explosions, NO text, 16:9.
  ```
* **尾帧 `S03_B`（同对话续画指令）**：
  ```text
  Generate S03_B by panning slightly up-left and pulling back from S03_A in the exact same orbital space style.
  The blinding white solar glare in the upper-left now illuminates an overwhelming, dense, chaotic river of jagged dark ice-and-rock asteroids pouring unseen out of the sunlight toward Earth's blue curved limb in the lower right. Hundreds of shadowed boulders and swirling icy debris trails create terrifying scale, backlit with razor-thin silver-blue rim light. Earth remains intact below, about to be overwhelmed. NO fireballs, NO lasers, NO text, 16:9.
  ```
* **Flow 视频提示词（`S03_A → S03_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation, stark cosmic contrast transitioning from serene cobalt blue to blinding high-contrast solar glare. One continuous 10-second slow sweeping orbital camera pan upward-left and gradual pull-back. Starting above Earth's peaceful curved blue limb as light dust glints quietly in vacuum, the camera shifts toward the harsh pale-white sun flare in the upper left; as exposure adjusts, thousands of dark jagged icy boulders and dense rock-and-ice debris streams emerge abruptly out of the blinding glare, pouring relentlessly toward Earth with heavy silent inertia. Sharp icy rim light on backlit asteroid silhouettes, smooth eased motion, no cuts, no explosions yet, no spaceships, no readable text.
  ```

---

### S04｜主碎片流撞击外海（10 秒，对应漫画第 2 格）

* **审核要点**：严格对齐 `OpeningComicIntro.png` 中间格的末日压迫感——黑压压的积雨云与碎屑尾迹斜切海岸天际，外海地平线连续升起刺眼水汽闪光与高耸蒸汽柱，城市尚在但天色剧变。
* **首帧 `S04_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S04_A in the exact theatrical 2D anime film style of Panel 2 of the reference image.
  Scene: High hillside overlook looking across a sprawling modern coastal bay city toward the distant ocean horizon. Heavy charcoal-gray storm clouds blanket the sky as dozens of blazing orange-and-white meteor streaks slice diagonally downward through the clouds toward the open sea far offshore. In the foreground, dark green windblown hillside foliage frames the city's silhouette below. Ominous tense stillness just before impact, NO explosions in the city yet, NO text, 16:9.
  ```
* **尾帧 `S04_B`（同对话续画指令）**：
  ```text
  Generate S04_B by continuing directly from S04_A from the exact same hillside camera position in the same 2D anime film style.
  Now multiple massive icy fragments have struck the distant outer ocean along the horizon: towering blinding-white geysers of vaporized seawater and shockwave mist erupt vertically from the sea surface, casting eerie pale-orange reflections across the dark ocean and underbelly of the charcoal clouds, while dozens more burning streaks continue descending behind them. The coastal city below sits silhouetted in tense shadow as distant sea swells begin churning. No lava, no sci-fi beams, no text, 16:9.
  ```
* **Flow 视频提示词（`S04_A → S04_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation in dramatic disaster-film style, charcoal storm grays contrasted against fiery orange meteor trails and blinding white ocean steam plumes. Steady wide shot from a hillside overlook above the coastal bay city with a subtle camera tremble on distant impact. Blazing ice-and-rock fragments streak rapidly downward through thick dark clouds and slam successively into the distant outer ocean horizon, sending massive vertical geysers of seawater and boiling white steam billowing high into the sky, illuminating the dark sea surface and cloud bellies with flickering amber light. Wind sweeps the foreground hillside leaves. Smooth realistic water physics, no lava, no city buildings exploding directly, no cuts, no text.
  ```

---

### S05｜海啸吞没沿海旧城（10 秒，对应漫画第 3 格）

* **审核要点**：严格对齐 `OpeningComicIntro.png` 第 3 格——铺天盖地的深青白沫巨浪越过海堤吞没城区低矮楼宇，前景岩石高地上背着登山包的幸存者无力地注视着家园被淹。
* **首帧 `S05_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S05_A in the exact theatrical 2D anime film style of Panel 3 of the reference image.
  Scene: View from a rugged dark basalt coastal headland covered in wet grass and scrub. In the right foreground, 3 survivors wearing raincoats and emergency backpacks kneel/crouch on the high rocky ridge looking out in shock. Below them, the coastal highway bridge and low-rise waterfront city sit under stormy dark gray skies as a colossal towering wall of dark teal ocean wave with roaring white foam rises above the distant breakwater, just beginning to surge inland. Crisp anime water details, NO gore, NO text, 16:9.
  ```
* **尾帧 `S05_B`（同对话续画指令）**：
  ```text
  Generate S05_B by continuing directly from S05_A with a slight camera pull-back and subtle upward crane on the same rocky cliff in the 2D anime film style.
  The colossal foaming tsunami wave has crashed deep into the coastal city below, churning dark muddy seawater and white spray around mid-rise concrete buildings, submerged bridges, and isolated rocky sea stacks; heavy sea mist fills the air as rain begins falling. On the safe rocky ridge in the right foreground, the survivors cling together against the gale, staring at the flooded city. Realistic water scale, no corpses, no readable signs, 16:9.
  ```
* **Flow 视频提示词（`S05_A → S05_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation matching dramatic sea-disaster cinema, cold stormy slate-blue, churning dark teal water, and crisp white sea foam. Slow steady camera pull-back and slight elevation behind the crouched survivors on the wet rocky cliff overlooking the coastal city. The colossal wall of dark ocean water surges violently over the breakwater, flooding across highways and swirling around concrete apartment blocks in roaring torrents of muddy foam and mist. Heavy sea wind whips the grass and raincoats of the survivors in the foreground while ocean spray rises through the air. Weighty water momentum, no cuts, no sudden morphing, no gore, no readable text.
  ```

---

### S06｜电网与卫星失灵，沿海救援站响起短波信号（8 秒，主角正式登场）

* **审核要点**：**主角第一次出场**（此时穿褪色锈橙防水外套 + 暗红救生衣 + 左臂纯白三角布章完全合情合理！）；从窗外一片片熄灭的城市灯火拉回昏暗应急室，只剩老式短波电台泛着微弱绿光。
* **首帧 `S06_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S06_A in the exact theatrical 2D anime film style of the reference image.
  Scene: Inside a cramped, functional coastal rescue station command room on a stormy night. Through a rain-streaked window on the left, a half-flooded distant town goes dark as sections of streetlights flicker out under rain clouds. On a scarred metal desk, modern computer monitors display blank static snow and dead red power indicators. Standing beside the desk in profile is our Heroine (30-year-old woman, short tousled black hair, faded rust-orange waterproof rescue jacket over a dark red life vest, plain blank white triangular patch on her left sleeve), one hand resting near a rugged analog shortwave radio transceiver whose small dial glows faint warm green. Dim amber emergency lantern lighting, waterproof rolled sea charts on the wall, NO readable text, 16:9.
  ```
* **尾帧 `S06_B`（同对话续画指令）**：
  ```text
  Generate S06_B by pushing smoothly closer into a tight medium close-up inside the exact same room from S06_A.
  The outside city lights are now completely blacked out, and the modern monitors are dead black. The heroine leans attentively over the glowing green analog shortwave transceiver, pressing a wired headset to her ear with one hand while her other hand places a finger onto a folded waterproof coastal sea chart (abstract coastline contour lines only, NO readable text). Her expression is calm, weary, and resolute; a second rescue crewmember in dark rain gear stands ready near the door behind her holding a waterproof gear bag. Consistent face, hair, rust-orange jacket, dark red life vest, and blank white triangular patch on left sleeve. 16:9.
  ```
* **Flow 视频提示词（`S06_A → S06_B`, Omni 1.2 Flash, 8s）**：
  ```text
  Theatrical 2D anime film animation, moody rainy night lighting transitioning from dying cold monitor static to dim amber lantern light and faint green radio glow. One smooth 8-second push-in inside the stormy coastal rescue station. Outside the rain-lashed window, the last distant town lights black out completely while the desk monitors go dark. The 30-year-old female rescuer in her faded rust-orange waterproof jacket and dark red life vest presses a shortwave headset to her ear, turns the radio tuning knob slightly as the green dial pulses faintly, and places her finger steadily onto the blank sea chart. Natural dark eyes focused on her task, never looking at the camera, rain streaking down the glass, no cuts, no readable text.
  ```

---

### S07｜暴雨与孤舟：灾后第一次海上救援（8 秒）

* **审核要点**：首次清晰展示游戏里的**橙白方正小救援船**（深蓝船底、舱顶两盏圆灯、船尾外挂机）以及**主角+船员协作救人**，打牢玩家“从一艘救援船出发”的情感锚点。
* **首帧 `S07_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S07_A in the exact theatrical 2D anime film style of the reference image.
  Scene: Low angle right beside a small, practical weathered orange-and-white coastal rescue boat (dark blue lower hull, boxy wheelhouse cabin with two round roof floodlights shining softly through mist, salt stains and scratches) rocking on choppy dark-teal ocean waves under steady drizzle. Leaning over the starboard gunwale in the center is our Heroine (exact same short wet black hair, faded rust-orange waterproof jacket, dark red life vest, plain blank white triangular patch on left sleeve), preparing to toss an orange life ring attached to a rope toward a half-submerged capsized skiff nearby where a shivering survivor clings to the hull. A male crewmate behind her holds the safety line ready. Foggy flooded ruins barely visible in far background, NO readable boat numbers or text, 16:9.
  ```
* **尾帧 `S07_B`（同对话续画指令）**：
  ```text
  Generate S07_B by continuing directly from S07_A seconds later on the exact same rescue boat in the same choppy rainy sea and 2D anime film style.
  The drenched survivor now grips the orange life ring tight against the side of the rescue boat while the heroine and her crewmate lean back together, hauling the survivor firmly up toward the gunwale with clear physical weight and splashed seawater spray. The boat's two roof floodlights cut softly through the falling rain and mist. Consistent character faces, outfits, white triangular left sleeve patch, and boxy orange-white boat design, NO text, 16:9.
  ```
* **Flow 视频提示词（`S07_A → S07_B`, Omni 1.2 Flash, 8s）**：
  ```text
  Theatrical 2D anime film animation with dynamic ocean wave physics and fine falling rain streaks, cool stormy teal palette with warm floodlight glow and rust-orange jacket accent. One continuous 8-second handheld boat-side tracking shot gently bobbing with the swell. The female rescuer in the faded rust-orange jacket and dark red life vest tosses the orange life ring across the choppy water to the stranded survivor clinging to the overturned skiff; assisted by her crewmate gripping the safety line, she leans back with real physical weight to pull the survivor safely toward the boat's gunwale as sea spray splashes against the dark blue hull. Smooth boat rocking, consistent boat shape, no cuts, no readable text.
  ```

---

### S08｜岁月流逝：海平面逐年缓慢上涨，旧城沉入潮线之下（10 秒）

* **审核要点**：体现《潮线之上》的核心科幻设定——不是一天淹没，而是**富冰残片持续补水与极端降雨造成海平面多年缓慢爬升**。同一机位，旧码头/石墙上的水位随季节更替一截一截爬高，海岸线彻底变成群岛与水下废墟。
* **首帧 `S08_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S08_A in the exact theatrical 2D anime film style of the reference image.
  Scene: Fixed wide-angle view from an elevated stone landing looking down a weathered coastal concrete sea wall and old harbor street beside calm slate-gray sea. The water sits low against the lower third of the stone wall, leaving a faint old damp stain; weathered wooden mooring posts stand dry near the top, and low coastal shops and a rusted streetlamp (no readable text) remain above the waterline under overcast gray daylight. Distant misty green hills rise far beyond the bay. Clean anime architectural detail, NO text or numbers, 16:9.
  ```
* **尾帧 `S08_B`（同对话续画指令）**：
  ```text
  Generate S08_B from the EXACT SAME fixed camera position, framing, and distant hills as S08_A, showing several years later in the same 2D anime film style.
  Now the calm deep-teal ocean has risen steadily by several meters: the stone sea wall and street are completely submerged beneath clear dark water, barnacles and pale salt marks line the higher stone retaining wall, only the very tips of the wooden mooring posts and the upper windows/rooftops of the old coastal buildings poke quietly above the glassy sea surface, and our small orange-and-white rescue boat glides slowly in the middle distance past the flooded ruins toward the distant hills under cool misty light. Quiet melancholic time passage, NO text, 16:9.
  ```
* **Flow 视频提示词（`S08_A → S08_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation, fixed tripod time-lapse across several years, subtle shifting weather lighting from overcast storm gray to pale winter mist and cool teal twilight. The camera remains locked on the exact same coastal sea wall and harbor street with only an almost imperceptible slow breath-like zoom. Over 10 seconds, clouds race smoothly across the sky and rain falls in gentle pulses as the sea level creeps steadily and inexorably upward along the stone wall—first lapping over the street pavement, then submerging doorways and mooring posts as salt marks and moss climb the stone, until the old coastal town rests quietly half-submerged beneath deep-teal water and the small orange-and-white rescue boat passes gently through the new waterway. Peaceful, melancholic passage of time, no sudden tidal waves, no morphing buildings, no cuts, no text.
  ```

---

### S09｜沿短波信号绕过沉船，发现可建立前哨的高地岛（10 秒）

* **审核要点**：精准衔接 `LastLandfall_Scenario_Progression.md` 开局：**玩家 + 两名船员 + 小救援艇**侦测附近求救信号赶来，发现目标已是东侧浅滩上的**沉船**，而前方晨雾中露出一座可停靠建站的**崎岖高地主岛**！
* **首帧 `S09_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S09_A in the exact theatrical 2D anime film style of the reference image.
  Scene: Low three-quarter stern tracking view behind our small weathered orange-and-white rescue boat (dark blue hull, boxy wheelhouse with two round roof lights, outboard motor churning a gentle white wake) gliding slowly through cold pale-gray morning fog across deep-teal ocean. Inside the open rear cabin doorway, the Heroine (faded rust-orange jacket, dark red life vest) stands at the helm looking forward while two crew members sit quietly near strapped supply crates, waterproof toolboxes, and a shortwave antenna. Just off to the right midground in shallow rocky mist lies the tilted, half-sunken rusted hull of an abandoned shipwreck—silent and empty. Ahead, thick sea fog still hides the horizon. Crisp anime water & mist lighting, NO text, 16:9.
  ```
* **尾帧 `S09_B`（同对话续画指令）**：
  ```text
  Generate S09_B by continuing smoothly forward past the fog from S09_A in the exact same 2D anime film style.
  The small orange-and-white rescue boat (now slightly smaller in the lower foreground leaving a clean wake) has glided past the foggy shipwreck into a clearing strait: parting silver mist and a soft break of warm amber dawn sunlight reveal a rugged, multi-tiered rocky highland island rising out of the teal sea ahead—featuring dark basalt cliffs, layered grassy plateaus, wind-sculpted coastal pine trees, a narrow rocky beach cove suitable for a wooden landing dock, and an old dark lighthouse ruin perched on an outlying sea rock on the far side. Hopeful, grounded pioneer atmosphere, NO modern buildings yet, NO skyscrapers, NO text, 16:9.
  ```
* **Flow 视频提示词（`S09_A → S09_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation, cool misty teal ocean opening into soft golden-amber morning light breaking through parting sea fog. One continuous 10-second low tracking shot following just behind the small orange-and-white rescue boat as it slices smoothly through gentle morning swells with a soft white wake. Inside the cabin, the female rescuer at the helm and two crew members gaze ahead past the half-sunken tilted wreck of a coastal ship resting silently on the misty rocky shoal to their right. As the boat clears the drifting fog bank, the veil parts to reveal a rugged multi-tiered rocky highland island ahead with dark cliffs, green pine ridges, a natural landing cove, and a distant ruined stone lighthouse on an outlying rock. Calm, hopeful discovery, steady boat motion, no cuts, no readable text.
  ```

---

### S10｜高地落脚与开局留白（10 秒，无缝切入游戏《潮线之上》）

* **审核要点**：镜头越过驶近岸边的小艇缓缓升空至游戏实机斜俯视视角（45° 等距/广角岛屿俯瞰），金色的微弱晨光照亮高地平台与岸边岩滩，最后 2 秒保持静态构图与天空/海面留白，方便 Unity 叠加标题与淡入实机操作界面。
* **首帧 `S10_A`（ChatGPT 提示词）**：
  ```text
  Generate 16:9 widescreen image S10_A in the exact theatrical 2D anime film style of the reference image.
  Scene: Medium aerial view just behind and above the small orange-and-white rescue boat as it approaches the rocky shoreline cove of the rugged highland island (matching S09_B: layered basalt terrain ledges, windblown pine trees, sparse bushes, natural stream gully, and untouched flat highland buildable terraces). Warm amber dawn light illuminates the eastern ridge against cool slate-blue sea mist. Untouched natural island ready to build upon, NO buildings yet, NO text, 16:9.
  ```
* **尾帧 `S10_B`（同对话续画指令）**：
  ```text
  Generate S10_B by pulling the camera high and tilting downward into a grand elevated 45-degree isometric-like establishing shot of the exact same highland island from S10_A in the 2D anime film style.
  The tiny orange-and-white rescue boat sits moored quietly at the rocky shoreline cove below, looking small against the multi-tiered rocky highland island surrounded by vast open deep-teal ocean, with the half-submerged shipwreck visible on an eastern islet and a ruined lighthouse rock further out. Golden morning sunbeams pierce soft clouds onto the central highland plateau, while the upper-left open misty sea and sky offer generous calm negative space for a game title overlay. Peaceful, enduring hope, NO UI, NO buildings, NO text, 16:9.
  ```
* **Flow 视频提示词（`S10_A → S10_B`, Omni 1.2 Flash, 10s）**：
  ```text
  Theatrical 2D anime film animation, sweeping tranquil establishing shot in cool teal ocean tones bathed in soft golden-amber sunrise beams. One continuous 10-second graceful aerial crane pull-up and slow slight orbit rising above the orange-and-white rescue boat as it glides gently up to the rocky shoreline cove and comes to rest. As the camera climbs into a wide high-angle view overlooking the entire rugged highland island—revealing its multi-tiered buildable plateaus, pine trees, neighboring shipwreck islet, and distant ruined lighthouse—warm sunlight breaks slowly across the central ridge while gentle waves lap the rocks below. The final 2 seconds settle into a serene, rock-steady composition with clean misty ocean negative space for a title card. Smooth eased finish, no buildings popping up, no UI, no text.
  ```

---

## 三、 后期剪辑与字幕配音节奏建议（接回 Unity）

1. **所有文字与字幕后期在剪辑软件加**（禁止 AI 画面生成字符）。建议旁白克制，只在转折点落 6 句短字幕：
   - **S01**：*“起初，我们只看见几颗游离的碎冰。”*
   - **S02**：*“第一轮拦截很顺利——于是全世界都松了口气。”*
   - **S03–S04**：*“没有人注意到，太阳眩光背后正拖着整片崩解的冰核主云。”*
   - **S05–S06**：*“防线来不及反应。海岸倾覆，电网与卫星相继归于沉寂。”*
   - **S07–S08**：*“灾难并没有停在第一场海啸——冰水不断落下，潮线年复一年向上攀升。”*
   - **S09–S10**：*“顺着最后一段短波信号，我们找到了这片仍露出海面的高地。这里，就是人类最后的落脚点。”*
2. **音乐情绪线**：
   - `S01–S02`：极简钢琴 + 微微上扬的弦乐暖意（虚假安心）；
   - `S03–S05`：低频大提琴嗡鸣骤起，S04 撞击转无声压迫，S05 涌入低沉轰鸣；
   - `S06–S08`：收为孤独的短波电台底噪 + 轻雨声 + 稀疏大提琴独奏；
   - `S09–S10`：晨光破云时加入温和的木吉他/钢琴和弦，在 S10 定格处平稳淡出接入游戏主界面或开局场景。
