"""Add new fields for codigo_barras, sale_type, weight, client_id

Revision ID: add_new_fields
Revises: 
Create Date: 2026-04-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_new_fields'
down_revision = '9b0daa48fa7e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Products: add codigo_barras, sale_type, weight_in_stock, min_weight
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('codigo_barras', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('sale_type', sa.String(20), nullable=True, server_default='UNIT'))
        batch_op.add_column(sa.Column('weight_in_stock', sa.Numeric(10, 3), nullable=True))
        batch_op.add_column(sa.Column('min_weight', sa.Numeric(10, 3), nullable=True, server_default='0.5'))
        batch_op.create_index('ix_products_codigo_barras', ['codigo_barras'])
        batch_op.create_index('ix_products_codigo_barras_store', ['codigo_barras', 'store_id'])
    
    # Sales: add client_id
    with op.batch_alter_table('sales') as batch_op:
        batch_op.add_column(sa.Column('client_id', sa.UUID(), sa.ForeignKey('clients.id', name='fk_sales_client_id'), nullable=True))
    
    # Sale Items: add weight
    with op.batch_alter_table('sale_items') as batch_op:
        batch_op.add_column(sa.Column('weight', sa.Numeric(10, 3), nullable=True))
    
    # Pets: add photo_url
    with op.batch_alter_table('pets') as batch_op:
        batch_op.add_column(sa.Column('photo_url', sa.Text(), nullable=True))
    
    # Stores: add asaas_customer_id (for Pix)
    with op.batch_alter_table('stores') as batch_op:
        batch_op.add_column(sa.Column('asaas_customer_id', sa.String(255), nullable=True))
    
    # Create schedule_blocks table if not exists
    op.create_table('schedule_blocks',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('store_id', sa.UUID(), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Create pet_notes table if not exists
    op.create_table('pet_notes',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('pet_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )


def downgrade() -> None:
    op.drop_column('stores', 'asaas_customer_id')
    op.drop_column('pets', 'photo_url')
    op.drop_column('sale_items', 'weight')
    op.drop_column('sales', 'client_id')
    op.drop_table('pet_notes')
    op.drop_table('schedule_blocks')
    op.drop_index('ix_products_codigo_barras_store')
    op.drop_index('ix_products_codigo_barras')
    op.drop_column('products', 'min_weight')
    op.drop_column('products', 'weight_in_stock')
    op.drop_column('products', 'sale_type')
    op.drop_column('products', 'codigo_barras')