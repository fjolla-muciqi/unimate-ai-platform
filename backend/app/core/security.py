from datetime import datetime, timedelta, timezone

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.scalar(
        select(User).where(User.id == int(user_id))
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user
def require_roles(*roles: UserRole):
    """Ndërton një dependency që lejon vetëm rolet e dhëna.

    Deri tani ekzistonte vetëm `require_admin`, prandaj një profesor
    trajtohej saktësisht si student në çdo endpoint. Ky konstruktor e
    bën rolin e nevojshëm të dukshëm te vetë deklarata e endpoint-it.
    """

    allowed = set(roles)

    def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Access requires one of: "
                    + ", ".join(sorted(role.value for role in allowed))
                    + "."
                ),
            )

        return current_user

    return dependency


require_admin = require_roles(UserRole.ADMIN)

require_professor = require_roles(UserRole.PROFESSOR)

# Ngarkimi i dokumenteve i takon stafit akademik, jo vetëm adminit —
# siç e kërkon specifikimi i fazës CORE.
require_staff = require_roles(UserRole.ADMIN, UserRole.PROFESSOR)