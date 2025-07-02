"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('internal_tran_id', sa.String(length=50), nullable=False),
        sa.Column('requested_foreign_currency', sa.String(length=3), nullable=False),
        sa.Column('requested_foreign_amount', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('recipient_paypal_email', sa.String(length=255), nullable=False),
        sa.Column('payment_purpose', sa.Text(), nullable=True),
        sa.Column('exchange_rate_bdt', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('calculated_bdt_amount', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('service_fee_bdt', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('total_bdt_amount', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('sslcz_tran_id', sa.String(length=100), nullable=True),
        sa.Column('sslcz_val_id', sa.String(length=100), nullable=True),
        sa.Column('sslcz_received_bdt_amount', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('sslcz_store_amount_bdt', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('sslcz_card_type', sa.String(length=50), nullable=True),
        sa.Column('sslcz_bank_tran_id', sa.String(length=100), nullable=True),
        sa.Column('sslcz_payment_method', sa.String(length=50), nullable=True),
        sa.Column('sslcz_ipn_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sslcz_validation_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('paypal_payout_tran_id', sa.String(length=100), nullable=True),
        sa.Column('paypal_payout_status', sa.String(length=50), nullable=True),
        sa.Column('paypal_payout_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('bdt_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payout_initiated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    op.create_index(op.f('ix_transactions_internal_tran_id'), 'transactions', ['internal_tran_id'], unique=True)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)

    # Create transaction_status_history table
    op.create_table('transaction_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('old_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transaction_status_history_id'), 'transaction_status_history', ['id'], unique=False)

    # Create payment_limits table
    op.create_table('payment_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('currency_code', sa.String(length=3), nullable=False),
        sa.Column('daily_limit', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('monthly_limit', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('yearly_limit', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('current_daily_used', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('current_monthly_used', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('current_yearly_used', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('daily_reset_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('monthly_reset_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('yearly_reset_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_limits_id'), 'payment_limits', ['id'], unique=False)
    op.create_index(op.f('ix_payment_limits_user_id'), 'payment_limits', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_payment_limits_user_id'), table_name='payment_limits')
    op.drop_index(op.f('ix_payment_limits_id'), table_name='payment_limits')
    op.drop_table('payment_limits')
    op.drop_index(op.f('ix_transaction_status_history_id'), table_name='transaction_status_history')
    op.drop_table('transaction_status_history')
    op.drop_index(op.f('ix_transactions_user_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_status'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_internal_tran_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
