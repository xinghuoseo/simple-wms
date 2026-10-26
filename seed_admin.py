"""创建初始管理员账号：python seed_admin.py"""
import getpass

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def main():
    engine = create_engine(DATABASE_URL)
    with sessionmaker(bind=engine)() as db:
        if db.query(User).first() is not None:
            print("已有用户，跳过创建。")
            return
        username = input("管理员用户名 [admin]: ").strip() or "admin"
        password = getpass.getpass("密码 [admin123]: ") or "admin123"
        db.add(User(username=username, password_hash=pwd_context.hash(password), real_name="管理员"))
        db.commit()
        print(f"已创建用户 {username}，请尽快登录修改密码。")

if __name__ == "__main__":
    main()
