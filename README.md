# SAM (Segment Anything Model) 图像与视频分割工具

## 项目简介

本项目是基于 Meta AI 的 SAM (Segment Anything Model) 开发的图像与视频分割工具，支持多种分割模式，包括静态图像分割、视频分割和动态交互视频分割。

### 功能特性

- 🖼️ **图像分割**：支持单张图像的语义分割
- 🎬 **视频分割**：支持视频文件的批量分割处理
- 🎮 **动态交互视频分割**：支持交互式视频分割，可跟踪多个目标
- ⚙️ **多模型支持**：支持原始 SAM 模型、SAM2 模型和轻量级 Mobile SAM 模型
- 📊 **详细日志**：完整的日志记录，便于调试和性能分析
- 🎨 **可视化输出**：支持分割结果的可视化和保存

## 目录结构

```angular2html
.
├── config
├── logs
│   └── 2025-12-05
├── outputs
│   ├── sam_1
│   │   └── jpg
│   ├── sam_2
│   │   └── jpg
│   └── sam_mobile
│       └── jpg
├── runs
│   └── segment
│       └── predict
├── test_data
├── tools
│   ├── 2025-12-01
│   ├── logs
│   │   └── 2025-12-01
│   └── __pycache__
└── weights
```


## 系统要求

- **操作系统**：Ubuntu 20.04
- **Python 版本**：Python 3.9+
- **硬件要求**：
  - CPU: 4核以上
  - GPU: NVIDIA GPU (推荐RTX 3090/4090，支持CUDA 11.3+)
  - 内存: 16GB以上
  - 显存: 8GB以上

## 安装步骤

### 1. 克隆代码仓库

```bash
git clone git@github.com:FishXDDD/SAM.git
cd SAM
```

### 2. 创建并激活虚拟环境

```bash
# 使用 conda 创建虚拟环境
conda create -n sam python=3.9
conda activate sam
```

### 3. 安装依赖包

```bash
pip install -r requirements.txt
```


## 使用说明

### 命令行参数

```bash
python predict.py [--config CONFIG_PATH] [--log_level LOG_LEVEL] [--mode MODE]
```

| 参数 | 类型 | 默认值 | 可选值 | 说明 |
|------|------|--------|--------|------|
| --config | str | ./config/sam_mobile.yaml | ./config/sam_1.yaml, ./config/sam_2.yaml, ./config/sam_mobile.yaml | 配置文件路径 |
| --log_level | str | DEBUG | DEBUG, INFO, WARNING, ERROR | 日志级别 |
| --mode | str | img | img, video, DynVideo | 分割模式 |

### 配置文件说明

配置文件采用 YAML 格式，主要包含以下参数：

```yaml
# 模型配置
model_path: "./weights/mobile_sam.pt"  # 模型权重路径

# 输入输出配置
input_jpg_path: "test_data/dog.jpg"    # 图像输入路径
input_mp4_path: "test_data/COOKIE.mp4"  # 视频输入路径
preprocess_output_path: "outputs/sam_mobile/preprocess"  # 预处理输出路径
output_path: "outputs/sam_mobile/jpg"  # 最终输出路径

# 分割参数
points: [[2688, 1512]]  # 分割点坐标 ([[x1, y1], [x2, y2], ...])
bboxes: null            # 边界框 ([[x1, y1, x2, y2], ...])
labels: null            # 标签 ([0, 1, ...])
frame_interval: 1       # 视频帧处理间隔
```

### 运行示例

#### 1. 图像分割示例

```bash
# 使用 Mobile SAM 模型分割图像
python predict.py --config ./config/sam_mobile.yaml --mode img

# 使用 SAM 1.0 模型分割图像
python predict.py --config ./config/sam_1.yaml --mode img
```

#### 2. 视频分割示例

```bash
# 使用 SAM 2.0 模型分割视频
python predict.py --config ./config/sam_2.yaml --mode video
```

#### 3. 动态交互视频分割示例

```bash
# 使用 SAM 2.0 模型进行动态交互视频分割
python predict.py --config ./config/sam_2.yaml --mode DynVideo
```

## 模型说明



### 1. SAM 1.0 (sam_b.pt)

https://docs.ultralytics.com/zh/models/sam/

https://github.com/facebookresearch/segment-anything

### 2. SAM 2.0 (sam2_b.pt)

https://docs.ultralytics.com/zh/models/sam-2/

https://github.com/facebookresearch/sam2

### 3. Mobile SAM (mobile_sam.pt)

https://docs.ultralytics.com/zh/models/mobile-sam/

https://github.com/ChaoningZhang/MobileSAM

## 输出结果

分割结果保存在 `outputs/` 目录下，根据不同的模型和配置有不同的输出路径：

- 图像分割结果：保存为 JPG 格式，包含分割掩码和原始图像的叠加
- 视频分割结果：保存为视频文件或帧序列

## 注意事项

1. **配置文件格式**：
   - `points` 参数必须是 `[[x1, y1]]` 格式，不能是 `[]`
   - `bboxes` 和 `labels` 参数如果为 `null` 表示不使用，不能直接写 `None`

2. **模型选择**：
   - `DynVideo` 模式仅支持 SAM 2.0 模型
   - 视频分割模式推荐使用 SAM 2.0 模型

3. **性能优化**：
   - 对于大分辨率图像/视频，可以降低 `imgsz` 参数以提高推理速度
   - 可以调整 `frame_interval` 参数来减少视频处理的帧数

4. **日志管理**：
   - 日志文件保存在 `logs/` 目录下
   - 可以通过 `--log_level` 参数调整日志详细程度

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请联系项目维护者。

---

**更新日期**：2025-12-05
**版本**：v1.0