# 潮线之上（Last Landfall）

这是可直接由 Unity 打开的项目源码。当前这台电脑只负责编写和整理代码，不需要安装 Unity；把整个项目同步到装有 Unity 的电脑后再运行。

## 打开项目

在另一台电脑上用 Unity Hub 安装并打开 **Unity 6.3 LTS（6000.3）**，选择本项目根目录。Unity 会恢复 URP 17.3，并由 `Assets/Editor/LastLandfallProjectSetup.cs` 自动创建 URP 配置和原型场景。首次导入完成后打开 `Prototype` 场景，按 Play。

## 当前原型

- 斜俯视正交相机与椭圆形高地网格
- 水面包围高地
- 选择小屋后显示放置预览
- 水面、已占用地格和木材不足时不能放置
- 放置成功扣除 20 木材，初始木材为 100

操作：点击“小屋”按钮进入建造模式；在高地空地左键放置，右键退出。

当前界面和建筑都是灰盒占位。这个工作区没有 Unity 编辑器，因此源码尚未在此处编译或运行；需要在另一台电脑打开项目后做实际运行确认。

## 故事背景与开场

### 核心设定

一颗巨大的富冰天体掠过太阳系，在太阳潮汐作用下解体，留下与地球轨道相交的碎片流。人类起初只观测到零散的先导碎片，并成功将其拦截。各国因此相信防御系统有效，社会士气高涨。

不久后，密集的主碎片云突然到来。先前的拦截成功让人类低估了后续威胁；碎片从难以观测的方向逼近，拦截和预警都来不及应对。大量碎片进入大气并撞击海洋，引发连续冲击、海啸和沿海城市崩塌。卫星、电网和海底通信线路遭到破坏，全球互联网长期不稳定。

灾难并非一次海啸后就结束。残余碎片仍会不定期经过地球，任何一天、任何区域都可能遇袭；富冰碎片持续进入地球环境，带来新的水量和极端降雨，海平面因此逐年上涨。海上航行与高地生存成为日常，安全的高地也成为人类重建聚落的基础。持续补水和多年上涨属于本作的科幻前提。

### 人类社会与玩家

集中式救援逐渐演变为区域救援联盟和高地自治据点。卫星网络或电力中断时，人们靠短波无线电、船只和信使传递附近的求救任务。救援站以公共互助为目的，依靠居民生产、打捞和物资交换维持运作。

玩家从一艘救援船开始，亲自出海救援、探索和打捞；随后在一座可以旋转、四面扩建的高地上建立救援站。居民生产食物和物资，新来的幸存者带来技能与需求。随着船队和聚落发展，玩家逐步从亲自驾驶扩展到任务调度，同时仍能亲自出航。

故事模式围绕救援、招募、探索和聚落建设展开：玩家连接周边幸存者据点，寻找资源与新航路，并在不断上涨的海面上把一座高地建设成区域救援网络的中心。故事的目标不是恢复灾前世界，而是让更多人能在新环境中生活下去。

横版漫画风格开场概念图：`Assets/LastLandfall/Art/Previews/OpeningComicIntro.png`。

## 第一批 Blender 资产

`Tools/Blender/` 中的脚本会生成可继续编辑的 `.blend` 源文件，并导出 Unity 可导入的 FBX；Blender 没有 FBX 导出器时会使用内置 OBJ 导出器。批量生成时，在装有 Blender 的电脑上从项目根目录运行：

```powershell
.\Tools\Blender\generate_all_assets.ps1
```

如果 Blender 不在 `PATH`，传入 Blender 可执行文件路径：

```powershell
.\Tools\Blender\generate_all_assets.ps1 -BlenderExe "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
```

当前首批资产包括：居民小屋、温室、集水净水站、废料拆解工坊、发电站、仓库、救援指挥站、码头、单格道路模块，以及可拼接的高地地表/崖壁模块。模型以米为单位，地面原点为 `(0, 0, 0)`；建筑正面朝局部 `-Y`。建筑按材质合并网格以减少 Unity 渲染器数量。模块化地形分别导出为内部地格、直线崖边和外角崖边，可旋转拼接，避免整座岛固定成单一模型。道路模块占地严格为 1×1 格，包含直线、转角、T 字、十字和端头形状。

居民小屋生成器：`Tools/Blender/create_resident_hut.py`。其他资产脚本采用 `Tools/Blender/create_<asset>.py` 命名。FBX 输出到 `Assets/LastLandfall/Resources/Models/`，OBJ 备用输出以 `_OBJ.obj` 结尾；源文件保存在 `Assets/LastLandfall/Art/Source/`。

已在 Blender 5.2.2 LTS 运行全部生成脚本，生成 `.blend` 源文件和 FBX 模型，并在 `Assets/LastLandfall/Art/Previews/` 渲染了预览图。Unity 尚未在此处运行，因此 FBX 的 Unity 导入效果还需要在 Unity 编辑器中确认。现有灰盒放置原型只加载居民小屋；其他模型还需接入对应的建筑选单与占地规则。

## 项目结构

- `Assets/LastLandfall/Scripts/`：运行时原型代码
- `Assets/Editor/`：首次打开时自动配置 URP 和原型场景
- `Tools/Blender/`：用 Blender 程序化生成的游戏资产脚本
- `Packages/manifest.json`：Unity 包依赖
- `ProjectSettings/ProjectVersion.txt`：目标 Unity 版本
