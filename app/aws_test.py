import boto3


def main():
    sts = boto3.client("sts")

    identity = sts.get_caller_identity()

    print("AWS connection successful!")
    print(f"Account: {identity['Account']}")
    print(f"ARN: {identity['Arn']}")


if __name__ == "__main__":
    main()
