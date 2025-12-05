import os
import time
from loguru import logger as log

# 统一使用原生ANSI码，避免colorama版本兼容问题
class Color:
    # 基础颜色
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    # 样式
    BOLD = "\033[1m"
    RESET = "\033[0m"
    # 组合样式
    RED_BOLD = RED + BOLD

# 日志配置常量
class LogConfig:
    MAX_ROTATION_MB = 200  # 日志文件轮转大小（MB）
    LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} - {name} - {level} - {message}"  # loguru 格式
    BACKUP_COUNT = 5  # 保留备份文件数量
    ENCODING = "utf-8"  # 日志编码
    VALID_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]  # 合法日志级别
    LEVEL_PRIORITY = {  # 日志级别优先级（数值越大级别越高）
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3
    }

    # 日志颜色映射（WARNING改为红色，ERROR红色加粗区分）
    COLOR_MAP = {
        "DEBUG": Color.BLUE,          # 蓝色
        "INFO": Color.GREEN,          # 绿色
        "WARNING": Color.YELLOW,         # 红色（用户要求）
        "ERROR": Color.RED_BOLD,  # 红色加粗（区分WARNING）
        "RESET": Color.RESET     # 重置颜色
    }



class LogManager:
    def __init__(self, log_path="./logs/", run_mode="INFO", category="default"):
        """
        初始化 loguru 日志管理器
        :param log_path: 日志文件根路径
        :param run_mode: 控制台输出级别（控制控制台打印）："DEBUG" / "INFO" / "WARNING" / "ERROR"
        :param category: 日志分类（业务模块名）
        """
        # 校验初始级别合法性
        run_mode = run_mode.upper()
        if run_mode not in LogConfig.VALID_LEVELS:
            raise ValueError(f"初始日志级别无效：{run_mode}，合法级别：{LogConfig.VALID_LEVELS}")

        self.log_path = log_path  # 日志根目录
        self.run_mode = run_mode  # 控制台输出级别
        self.category = category  # 日志分类（业务模块名）

        # 确保日志根目录存在
        os.makedirs(self.log_path, exist_ok=True)

        # 保存 handler ID，用于后续动态移除/更新
        self.file_handlers = {}  # 键：日志级别标识，值：handler ID
        self.console_handler_id = None

        # 清空 loguru 原有 handler（避免重复输出）
        log.remove()

        # 1. 配置文件输出（始终保存所有级别日志）
        self._config_file_handlers()
        # 2. 配置控制台输出（按初始级别过滤打印）
        self._config_console_handler()

    def _get_log_file_path(self, mode):
        """生成日志文件路径"""
        # 1. 生成当天日期
        log_date = time.strftime("%Y-%m-%d")
        # 2. 日志日期目录：log_path/YYYY-MM-DD（创建在指定日志根路径下）
        date_dir = os.path.join(self.log_path, log_date)
        os.makedirs(date_dir, exist_ok=True)
        assert os.path.exists(date_dir), f"日志目录创建失败：{date_dir}"
        # 3. 生成文件名（包含分类、级别、日期）
        file_name = os.path.join(date_dir, f"{self.category}_{mode}_{log_date}.log")
        return file_name

    def _config_file_handlers(self):
        """配置文件输出：始终保存所有级别的日志（DEBUG/INFO/WARNING/ERROR）"""
        # ========== ERROR 日志 ==========
        if "error" in self.file_handlers:
            log.remove(self.file_handlers["error"])
        self.file_handlers["error"] = log.add(
            self._get_log_file_path("error"),
            rotation=f"{LogConfig.MAX_ROTATION_MB} MB",
            retention=LogConfig.BACKUP_COUNT,
            level="ERROR",
            format=LogConfig.LOG_FORMAT,
            encoding=LogConfig.ENCODING,
            filter=lambda record: record["extra"].get("category") == self.category
        )

        # ========== WARNING 日志 ==========
        if "warning" in self.file_handlers:
            log.remove(self.file_handlers["warning"])
        self.file_handlers["warning"] = log.add(
            self._get_log_file_path("warning"),
            rotation=f"{LogConfig.MAX_ROTATION_MB} MB",
            retention=LogConfig.BACKUP_COUNT,
            level="WARNING",
            format=LogConfig.LOG_FORMAT,
            encoding=LogConfig.ENCODING,
            filter=lambda record: record["extra"].get("category") == self.category
        )

        # ========== INFO 日志 ==========
        if "info" in self.file_handlers:
            log.remove(self.file_handlers["info"])
        self.file_handlers["info"] = log.add(
            self._get_log_file_path("info"),
            rotation=f"{LogConfig.MAX_ROTATION_MB} MB",
            retention=LogConfig.BACKUP_COUNT,
            level="INFO",
            format=LogConfig.LOG_FORMAT,
            encoding=LogConfig.ENCODING,
            filter=lambda record: record["extra"].get("category") == self.category
        )

        # ========== DEBUG 日志 ==========
        if "debug" in self.file_handlers:
            log.remove(self.file_handlers["debug"])
        self.file_handlers["debug"] = log.add(
            self._get_log_file_path("debug"),
            rotation=f"{LogConfig.MAX_ROTATION_MB} MB",
            retention=LogConfig.BACKUP_COUNT,
            level="DEBUG",
            format=LogConfig.LOG_FORMAT,
            encoding=LogConfig.ENCODING,
            filter=lambda record: record["extra"].get("category") == self.category
        )

    def _config_console_handler(self):
        """配置控制台输出：只打印当前run_mode及以上级别的日志"""
        # 移除旧的控制台handler
        if self.console_handler_id is not None:
            log.remove(self.console_handler_id)

        # 自定义彩色格式化函数（WARNING/ERROR整行染色）
        def colored_format(record):
            level = record["level"].name
            color = LogConfig.COLOR_MAP.get(level, LogConfig.COLOR_MAP["RESET"])
            reset = LogConfig.COLOR_MAP["RESET"]

            # 构造日志内容
            log_content = (
                f"{record['time'].strftime('%Y-%m-%d %H:%M:%S')} - {record['name']} - "
                f"{level} - {record['message']}"
            )

            # WARNING/ERROR 整行染色，其他级别仅级别名染色
            if level in ["WARNING", "ERROR"]:
                # 全色显示（整行）
                return f"{color}{log_content}{reset}\n"
            else:
                # 仅级别名染色
                return (
                    f"{record['time'].strftime('%Y-%m-%d %H:%M:%S')} - {record['name']} - "
                    f"{color}{level}{reset} - {record['message']}\n"
                )

        # 添加新的控制台handler
        self.console_handler_id = log.add(
            sink=lambda msg: print(msg, end=""),  # 控制台输出
            level=self.run_mode, # 控制台输出级别
            format=colored_format,
            filter=lambda record: record["extra"].get("category") == self.category
        )

    # ========== 对外暴露的核心接口 ==========
    def set_log_level(self, level):
        """
        核心接口：设置控制台输出级别，控制台不打印该级别以下的日志（但所有级别仍保存到本地文件）
        :param level: 目标控制台输出级别（DEBUG/INFO/WARNING/ERROR）
        :raises ValueError: 传入无效级别时抛出
        """
        # 1. 校验级别合法性
        level = level.upper()
        if level not in LogConfig.VALID_LEVELS:
            raise ValueError(f"无效的日志级别：{level}，合法级别：{LogConfig.VALID_LEVELS}")

        # 2. 如果级别未变化，无需处理
        if self.run_mode == level:
            log.bind(category=self.category).info(f"控制台日志级别已为 {level}，无需修改")
            return

        # 3. 更新运行模式
        self.run_mode = level
        # 4. 仅重新配置控制台handler（文件handler保持不变，始终保存所有级别）
        self._config_console_handler()

        # 日志记录级别变更
        log.bind(category=self.category).info(
            f"控制台日志级别已更新为：{level}（控制台不打印该级别以下的日志，但所有级别日志仍保存到本地）"
        )

    def debug(self, msg):
        """DEBUG 日志：始终保存到文件，仅当控制台级别为DEBUG时打印"""
        log.bind(category=self.category).debug(msg)

    def info(self, msg):
        """INFO 日志：始终保存到文件，仅当控制台级别≤INFO时打印"""
        log.bind(category=self.category).info(msg)

    def warning(self, msg):
        """WARNING 日志：始终保存到文件，仅当控制台级别≤WARNING时打印"""
        log.bind(category=self.category).warning(msg)

    def error(self, msg):
        """ERROR 日志：始终保存到文件+打印到控制台（最高级别）"""
        log.bind(category=self.category).error(msg)

    def get_current_level(self):
        """获取当前控制台输出级别"""
        return self.run_mode


if __name__ == "__main__":
    # 测试示例
    print("===== 初始化 DEBUG 级别（控制台打印所有级别） =====")
    log_manager = LogManager(log_path="./logs/", run_mode="DEBUG", category="TEST")
    print(f"当前控制台级别：{log_manager.get_current_level()}")
    log_manager.debug("这是DEBUG日志（保存+打印）")
    log_manager.info("这是INFO日志（保存+打印）")
    log_manager.warning("这是WARNING日志（保存+打印）")
    log_manager.error("这是ERROR日志（保存+打印）")

    # print("\n===== 设置控制台级别为 INFO（不打印DEBUG） =====")
    # log_manager.set_log_level("INFO")
    # print(f"当前控制台级别：{log_manager.get_current_level()}")
    # log_manager.debug("这是DEBUG日志（保存+不打印）")
    # log_manager.info("这是INFO日志（保存+打印）")
    # log_manager.warning("这是WARNING日志（保存+打印）")
    # log_manager.error("这是ERROR日志（保存+打印）")

    # print("\n===== 设置控制台级别为 WARNING（不打印DEBUG/INFO） =====")
    # log_manager.set_log_level("WARNING")
    # print(f"当前控制台级别：{log_manager.get_current_level()}")
    # log_manager.debug("这是DEBUG日志（保存+不打印）")
    # log_manager.info("这是INFO日志（保存+不打印）")
    # log_manager.warning("这是WARNING日志（保存+打印）")
    # log_manager.error("这是ERROR日志（保存+打印）")

    # print("\n===== 设置控制台级别为 ERROR（仅打印ERROR） =====")
    # log_manager.set_log_level("ERROR")
    # print(f"当前控制台级别：{log_manager.get_current_level()}")
    # log_manager.debug("这是DEBUG日志（保存+不打印）")
    # log_manager.info("这是INFO日志（保存+不打印）")
    # log_manager.warning("这是WARNING日志（保存+不打印）")
    # log_manager.error("这是ERROR日志（保存+打印）")
    #
    # # 验证文件保存：可以查看 ./logs/YYYY-MM-DD/TEST_*.log 文件，所有日志都已保存
    # print("\n提示：所有级别日志已保存到 ./logs 目录下，仅控制台输出按级别过滤！")