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

## 第一个 Blender 资产：居民小屋

小屋模型脚本位于 `Tools/Blender/create_resident_hut.py`。在装有 Blender 的电脑上，从项目根目录运行：

```powershell
blender --background --python Tools/Blender/create_resident_hut.py
```

脚本会生成可继续编辑的 `Assets/LastLandfall/Art/Source/ResidentHut.blend`，并导出 Unity 使用的 `Assets/LastLandfall/Resources/Models/ResidentHut.fbx`。模型按 1 Unity 单位约等于 1 米制作，地面为原点，屋顶和门阶控制在单格范围内；按材质合并网格，减少运行时渲染器数量。FBX 导入后，原型会自动加载该模型；FBX 尚未生成时仍显示灰盒房屋。

当前电脑没有 Blender，因此这里只有生成脚本，尚未生成或目视检查 `.blend` / `.fbx` 文件。首次在另一台电脑生成后，请在 Unity 中确认朝向、尺寸和材质，再继续调整。

## 项目结构

- `Assets/LastLandfall/Scripts/`：运行时原型代码
- `Assets/Editor/`：首次打开时自动配置 URP 和原型场景
- `Tools/Blender/`：用 Blender 程序化生成的游戏资产脚本
- `Packages/manifest.json`：Unity 包依赖
- `ProjectSettings/ProjectVersion.txt`：目标 Unity 版本
