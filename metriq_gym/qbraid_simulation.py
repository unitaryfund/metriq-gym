from dotenv import load_dotenv
from qbraid import QbraidProvider

load_dotenv()
provider = QbraidProvider()
print(provider.get_devices())
