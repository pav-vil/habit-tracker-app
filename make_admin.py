"""
Admin Management Script
Grant or revoke admin privileges for users
"""

import sys
from app import app
from models import db, User

def make_admin(email, revoke=False):
    """Grant or revoke admin privileges for a user."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()

        if not user:
            print(f"[ERROR] User with email '{email}' not found")
            print("\n[AVAILABLE USERS]:")
            all_users = User.query.all()
            for u in all_users:
                admin_status = "[ADMIN]" if u.is_admin else ""
                print(f"   - {u.email} {admin_status}")
            return False

        if revoke:
            user.is_admin = False
            db.session.commit()
            print(f"[SUCCESS] Admin privileges REVOKED for: {email}")
        else:
            user.is_admin = True
            db.session.commit()
            print(f"[SUCCESS] Admin privileges GRANTED to: {email}")
            print(f"\n[ADMIN DASHBOARD] You can now access the admin dashboard at:")
            print(f"   http://localhost:5000/payment/admin/dashboard")

        return True


def list_admins():
    """List all admin users."""
    with app.app_context():
        admins = User.query.filter_by(is_admin=True).all()

        if not admins:
            print("[INFO] No admin users found")
        else:
            print("[ADMIN USERS]:")
            for admin in admins:
                print(f"   - {admin.email} (ID: {admin.id})")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python make_admin.py <email>              # Grant admin")
        print("  python make_admin.py <email> --revoke      # Revoke admin")
        print("  python make_admin.py --list                # List all admins")
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_admins()
    elif len(sys.argv) >= 3 and sys.argv[2] == '--revoke':
        make_admin(sys.argv[1], revoke=True)
    else:
        make_admin(sys.argv[1])
