import logging
import sys

# 设置日志的配置
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

# 使用日志
logger = logging.getLogger(__name__)
