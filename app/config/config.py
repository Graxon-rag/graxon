from .env import Env


class Config:

    @staticmethod
    def is_dev_env():
        return Env.ENV_TYPE.lower() == "development" or Env.ENV_TYPE.lower() == "dev"

    @staticmethod
    def is_prod_env():
        return Env.ENV_TYPE.lower() == "production" or Env.ENV_TYPE.lower() == "prod"

    @staticmethod
    def is_test_env():
        return Env.ENV_TYPE.lower() == "test"
