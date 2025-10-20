import boto3
import sys
import os
import tomllib
import time
import logging
import time

from pathlib import Path

logger = logging.getLogger()
def init():
    with open("config.toml", "rb") as fp:
        config = tomllib.load(fp)

    log_destination = config.get("log_destination")

    if log_destination:
        logging.basicConfig(filename=f"{log_destination}", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger("init()")
    
    template_file = config.get("template_file")
    if not template_file:
        logger.critical("No template file configured")
        sys.exit()
    if not Path(template_file).is_file():
        logger.critical("Template file not found")
        sys.exit()
    os.environ["template_file"]=template_file

    output_file = config.get("output_file")
    if not output_file:
        logger.critical("No output file configured")
        sys.exit()
    
    os.environ["output_file"]=output_file



def main() -> None:

    init()
    logger = logging.getLogger("main()")

    logger.info("Starting")
    session = boto3.Session()

    iam = session.client("iam")
    sts = session.client("sts")

    username = sts.get_caller_identity()["Arn"].split("/")[-1]

    access_key_id = session.get_credentials().access_key

    response = iam.list_access_keys(UserName=username)
    
    for k in filter(lambda x: x["Status"] == "Inactive", response["AccessKeyMetadata"]):
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


    
    with open(os.environ["template_file"], "r") as fp:
        template = fp.read()

    template = (
        template.replace("${AWS_ACCESS_KEY_ID}", new_access_key_id)
        .replace("${AWS_SECRET_ACCESS_KEY}", new_secret_access_key)
    )



    logging.info("Updating env")
    with open(os.environ["output_file"], "w") as fp:
        fp.write(template)

    logging.info("Disable old access key")
    response = iam.update_access_key(
        UserName=username,
        AccessKeyId = access_key_id,
        Status = "Inactive"
    )
    logging.info("Done")
        


    



if __name__ == "__main__":
    main()