"""
RDS instance class matrix — us-east-1 on-demand pricing (update as needed).
Source: https://aws.amazon.com/rds/mysql/pricing/
"""

INSTANCE_MATRIX = {
    "db.t3.micro":   {"vcpu": 2,  "ram_gb": 1,    "max_conn": 66,   "price": 0.017},
    "db.t3.small":   {"vcpu": 2,  "ram_gb": 2,    "max_conn": 150,  "price": 0.034},
    "db.t3.medium":  {"vcpu": 2,  "ram_gb": 4,    "max_conn": 312,  "price": 0.068},
    "db.t3.large":   {"vcpu": 2,  "ram_gb": 8,    "max_conn": 648,  "price": 0.136},
    "db.t3.xlarge":  {"vcpu": 4,  "ram_gb": 16,   "max_conn": 1300, "price": 0.272},
    "db.t3.2xlarge": {"vcpu": 8,  "ram_gb": 32,   "max_conn": 2600, "price": 0.544},
    "db.m5.large":   {"vcpu": 2,  "ram_gb": 8,    "max_conn": 648,  "price": 0.192},
    "db.m5.xlarge":  {"vcpu": 4,  "ram_gb": 16,   "max_conn": 1300, "price": 0.384},
    "db.m5.2xlarge": {"vcpu": 8,  "ram_gb": 32,   "max_conn": 2600, "price": 0.768},
    "db.r5.large":   {"vcpu": 2,  "ram_gb": 16,   "max_conn": 1300, "price": 0.240},
    "db.r5.xlarge":  {"vcpu": 4,  "ram_gb": 32,   "max_conn": 2600, "price": 0.480},
    "db.r5.2xlarge": {"vcpu": 8,  "ram_gb": 64,   "max_conn": 5200, "price": 0.960},
    "db.r5.4xlarge": {"vcpu": 16, "ram_gb": 128,  "max_conn": 10000,"price": 1.920},
}

def hourly_price(instance_class):
    return INSTANCE_MATRIX.get(instance_class, {}).get("price")
