from minio import Minio

client = Minio(
    "localhost:9100",
    access_key="admin",
    secret_key="admin123",
    secure=False
)
client.fput_object("edurag", "demo.py", "./demo.py")
# client.fget_object("edurag", "价格1.png", "./price.png")
for each in client.list_objects("edurag"):
    print(each)