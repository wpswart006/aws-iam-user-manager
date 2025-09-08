import boto3
import time
import logging
import time

timestr = time.strftime("%Y%m%d.%H%M%S")
logging.basicConfig(filename=f"/var/log/aws-iam-user-manager/{timestr}", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger()
HEADER = "#>aws-iam-user-manager>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>."

def main() -> None:
    logger.info("Starting")
    session = boto3.Session()
    
    idx = -1
    with open("/etc/environment") as fp:
        for idx, line in enumerate(fp.readlines()):
            if line.strip() == HEADER:
                break

    if idx == -1:
        print("Credentials not in env, cannot update")
        return
    


    
    iam = session.client("iam")
    sts = session.client("sts")

    username = sts.get_caller_identity()["Arn"].split("/")[-1]

    access_key_id = session.get_credentials().access_key

    response = iam.list_access_keys(UserName=username)
    
    for k in filter(lambda x: x["Status"] == "Inactive", response["AccessKeyMetadata"]):
        """        {
            'UserName': 'string',
            'AccessKeyId': 'string',
            'Status': 'Active'|'Inactive'|'Expired',
            'CreateDate': datetime(2015, 1, 1)
        },"""
        logger.info("Disabling access key with id")
        iam.delete_access_key(
            UserName=k["UserName"],
            AccessKeyId=k["AccessKeyId"],
        )
    

    logging.info("Creating new access key")
    response = iam.create_access_key(
        UserName=username
    )

    new_access_key=response["AccessKey"]
    new_access_key_id = new_access_key["AccessKeyId"]
    new_secret_access_key = new_access_key["SecretAccessKey"]

    with open("/etc/environment", "r") as fp:
        content = fp.read()

    lines = content.split("\n")
    lines[idx+1] = f"export AWS_ACCESS_KEY_ID={new_access_key_id}"
    lines[idx+2] = f"export AWS_SECRET_ACCESS_KEY={new_secret_access_key}"

    content = "\n".join(lines)

    logging.info("Updating env")
    with open("/etc/environment", "w") as fp:
        fp.write(content)

    logging.info("Disable old access key")
    response = iam.update_access_key(
        UserName=username,
        AccessKeyId = access_key_id,
        Status = "Inactive"
    )
    logging.info("Done")
        


    



if __name__ == "__main__":
    main()