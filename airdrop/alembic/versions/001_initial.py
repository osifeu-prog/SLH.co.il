from alembic import op
import sqlalchemy as sa

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # בדיקה והוספת עמודות לטבלת users
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('users')]
    
    if 'username' not in columns:
        op.add_column('users', sa.Column('username', sa.String(), nullable=True))
    if 'referral_code' not in columns:
        op.add_column('users', sa.Column('referral_code', sa.String(), unique=True, nullable=True))
    if 'invited_by' not in columns:
        op.add_column('users', sa.Column('invited_by', sa.String(), nullable=True))
    if 'is_active' not in columns:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true'))
    if 'role' not in columns:
        op.add_column('users', sa.Column('role', sa.String(), server_default='user'))
