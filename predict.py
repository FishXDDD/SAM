import os.path
import cv2
from tools.log_mode import LogManager
from argparse import ArgumentParser
import time
import platform
import psutil
import torch
import yaml
from tqdm import tqdm
from typing import Dict, List

from ultralytics import SAM, __version__ as ultralytics_version
from ultralytics.models.sam import SAM2VideoPredictor, SAM2DynamicInteractivePredictor

class SAMPredictor:
    # 明确声明初始化需要的参数
    REQUIRED_INIT_PARAMS = ["model_path"]
    '''
    sam url: https://docs.ultralytics.com/zh/models/sam-2/#segment-with-prompts
    '''
    def __init__(self, model_path: str,
                 log_manager: LogManager = None,
                 mode: str = "image",
                 ):
        self.log_manager = log_manager

        self.mode =  mode
        load_model_start = time.time()
        self.log_manager.debug("🚀 开始加载SAM模型...")
        if mode in ["image", "video2img"]:
            self.log_manager.debug(f"🚀 模式为{mode}，处理图片模式...")
            self.model = SAM(model_path)
        elif mode == "video":
            self.log_manager.debug(f"🚀 模式为{mode}，model为{model_path}，处理视频模式...")
            overrides = dict(conf=0.25, task="segment", mode="predict", imgsz=1024, model=model_path)
            self.model = SAM2VideoPredictor(overrides=overrides)
            # overrides = dict(conf=0.25, task="segment", mode="predict", imgsz=1024, model="sam2_b.pt")
            # predictor = SAM2VideoPredictor(overrides=overrides)
        elif mode == "DynVideo":
            self.log_manager.debug(f"🚀 模式为{mode}，处理动态交互模式...")
            log_manager.info(f"model_path: {model_path}")
            # overrides = dict(conf=0.01, task="segment", mode="predict", imgsz=1024, model=model_path, save=False)
            # self.model = SAM2DynamicInteractivePredictor(overrides)
            overrides = dict(conf=0.01, task="segment", mode="predict", imgsz=1024, model="sam2_t.pt", save=False)
            self.model = SAM2DynamicInteractivePredictor(overrides=overrides, max_obj_num=10)

        load_model_elapsed = time.time() - load_model_start
        self.log_manager.debug(f"✅ 模型加载完成 | 耗时: {load_model_elapsed:.2f}s")


    def __call__(self, input_data,
                 bboxes: List[List[int]] = None,
                 points: List[List[int]] = None,
                 labels: List[int] = None):
        self.log_manager.debug(f"🚀 模型开始处理...")
        self.log_manager.debug(f"🚀 input_data: {input_data}")
        self.log_manager.debug(f"🚀 bboxes: {bboxes}")
        self.log_manager.debug(f"🚀 points: {points}")
        self.log_manager.debug(f"🚀 labels: {labels}")
        return self.model(input_data, points=points, labels=labels)


    def __del__(self):
        self.log_manager.info("✅ 模型已释放")


def get_system_info() -> Dict[str, str]:
    """采集系统/硬件核心信息（用于日志输出）"""
    # CPU信息
    cpu_info = {
        "型号": platform.processor() or "未知CPU",
        "核心数": f"{psutil.cpu_count(logical=True)} (逻辑) / {psutil.cpu_count(logical=False)} (物理)",
        "使用率": f"{psutil.cpu_percent(interval=0.1)}%"
    }

    # GPU信息（基于PyTorch）
    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info["数量"] = torch.cuda.device_count()
        gpu_info["型号"] = torch.cuda.get_device_name(0)
        gpu_info["CUDA版本"] = torch.version.cuda
        gpu_info["显存"] = f"{torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f}GB"
    else:
        gpu_info["状态"] = "无可用GPU / 使用CPU推理"

    # 内存信息
    mem = psutil.virtual_memory()
    mem_info = {
        "总内存": f"{mem.total / 1024 ** 3:.1f}GB",
        "可用内存": f"{mem.available / 1024 ** 3:.1f}GB",
        "使用率": f"{mem.percent}%"
    }

    # 基础环境信息
    basic_info = {
        "Python版本": platform.python_version(),
        "操作系统": f"{platform.system()} {platform.release()}",
        "Ultralytics版本": ultralytics_version,
        "PyTorch版本": torch.__version__,
        "推理设备": "GPU" if torch.cuda.is_available() else "CPU"
    }

    return {
        "=== 系统环境信息 ===": "",
        **basic_info,
        "\n=== CPU信息 ===": "",
        **cpu_info,
        "\n=== GPU信息 ===": "",
        **gpu_info,
        "\n=== 内存信息 ===": "",
        **mem_info
    }


def print_system_info():
    """格式化打印系统信息到日志"""
    sys_info = get_system_info()
    print("=" * 80)
    print("📋 系统/硬件环境信息")
    print("=" * 80)
    for key, value in sys_info.items():
        if "===" in key:
            print()
            print(f"\033[36m{key}\033[0m")  # 蓝色高亮分隔符（可选）
        else:
            print(f"  {key:<10}: {value}")
    print("=" * 80)


def format_inference_args(args_dict: Dict[str, any]) -> str:
    """格式化推理参数（用于日志输出）"""
    formatted = []
    for k, v in args_dict.items():
        if isinstance(v, list):
            formatted.append(f"{k}={[round(x, 2) if isinstance(x, float) else x for x in v]}")
        else:
            formatted.append(f"{k}={v}")
    return " | ".join(formatted)


def parse_args():
    """完善参数解析（补充缺失的model_path）"""
    parser = ArgumentParser(description="SAM (Segment Anything Model) 推理脚本")
    parser.add_argument("--config", type=str, default="./config/sam_2.yaml",
                        help="配置文件路径，默认: config.yaml")
    parser.add_argument("--log_level", type=str, default="DEBUG",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="日志级别，可选: DEBUG/INFO/WARNING/ERROR，默认: INFO")
    parser.add_argument("--mode", type=str, default="video2img",
                        choices=["img", "video2img", "video", "DynVideo"],
                        help="预处理模式，可选: 默认为空")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # 1. 初始化日志管理器
    args = parse_args()
    assert os.path.exists(args.config), f"配置文件 {args.config} 不存在"

    # 读取配置文件
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    assert os.path.exists(config["input_data_path"]), f"图片路径 {config['input_data_path']} 不存在"
    os.makedirs(config["output_data_path"], exist_ok=True)
    assert os.path.exists(config["output_data_path"]), f"输出路径 {config['output_data_path']} 不存在"

    log_manager = LogManager()
    log_manager.set_log_level(args.log_level)

    # 初始化预测器（仅传入所需参数）
    sam_predictor = SAMPredictor(model_path=config["model_path"], mode=args.mode, log_manager=log_manager,)

    # 2. 打印系统信息（日志头部）
    print_system_info()

    # 3. 打印解析后的参数
    log_manager.info("=" * 80)
    log_manager.info("⚙️  args参数")
    log_manager.info("=" * 80)
    for arg in vars(args):
        log_manager.info(f"  {arg:<12}: {getattr(args, arg)}")
    log_manager.info("=" * 80)
    log_manager.info("⚙️  config参数")
    log_manager.info("=" * 80)
    for key, value in config.items():
        log_manager.info(f"  {key:<12}: {value} type: {type(value)}")
    log_manager.info("=" * 80)

    # 4. 模型推理
    log_manager.info("🚀 开始推理...")
    results = sam_predictor(config["input_data_path"], bboxes=config["bboxes"], points=config["points"], labels=config["labels"])
    log_manager.info(f"✅ 推理完成，共处理 {len(results)} 个样本")

    if len(results) == 1:
        results[0].save(config["output_data_path"])
    elif len(results) > 1:
        log_manager.warning(f"⚠️  多个结果，请自行处理， 选择模式为 {args.mode}")
    else:
        log_manager.error("❌ 未处理任何样本")
