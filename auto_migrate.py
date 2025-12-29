"""
Automatic migration helper - runs on app startup
Safely adds missing columns without breaking the app
"""
from sqlalchemy import text, inspect


def auto_migrate_database(app, db):
    """
    Automatically add missing columns to the database.
    Runs safely on every app startup - won't break if column already exists.
    """
    with app.app_context():
        try:
            inspector = inspect(db.engine)

            # Check if habit table exists first
            if 'habit' not in inspector.get_table_names():
                print("[AUTO-MIGRATE] Fresh database - no migrations needed")
                return

            # Migration 1: Increase password_hash column length in user table
            user_columns = inspector.get_columns('user')
            password_hash_col = next((col for col in user_columns if col['name'] == 'password_hash'), None)

            if password_hash_col and password_hash_col.get('type').length and password_hash_col['type'].length < 255:
                print(f"[AUTO-MIGRATE] Increasing password_hash column from {password_hash_col['type'].length} to 255 characters...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255)'
                        ))
                        conn.commit()
                    print("[AUTO-MIGRATE] Successfully increased password_hash column length")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error altering password_hash column: {e}")

            # Migration 2: Add newsletter_subscribed column to user table
            user_column_names = [col['name'] for col in user_columns]
            if 'newsletter_subscribed' not in user_column_names:
                print("[AUTO-MIGRATE] Adding newsletter_subscribed column to user table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE "user" ADD COLUMN newsletter_subscribed BOOLEAN NOT NULL DEFAULT FALSE'
                        ))
                        conn.commit()
                    print("[AUTO-MIGRATE] Successfully added newsletter_subscribed column")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error adding newsletter_subscribed column: {e}")

            # Migration 3: Add dark_mode column to user table
            user_column_names = [col['name'] for col in user_columns]
            if 'dark_mode' not in user_column_names:
                print("[AUTO-MIGRATE] Adding dark_mode column to user table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE "user" ADD COLUMN dark_mode BOOLEAN NOT NULL DEFAULT FALSE'
                        ))
                        conn.commit()
                    print("[AUTO-MIGRATE] Successfully added dark_mode column")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error adding dark_mode column: {e}")

            # Migration 4: Check if longest_streak column exists in habit table
            habit_columns = [col['name'] for col in inspector.get_columns('habit')]

            if 'longest_streak' not in habit_columns:
                print("[AUTO-MIGRATE] Adding longest_streak column to habit table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE habit ADD COLUMN longest_streak INTEGER NOT NULL DEFAULT 0'
                        ))
                        conn.commit()

                    # Update existing habits to set longest_streak = streak_count
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'UPDATE habit SET longest_streak = streak_count'
                        ))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully added longest_streak column")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error adding longest_streak column: {e}")

            # Migration 5: Add 'why' column to habit table for motivation/reason tracking
            habit_columns = [col['name'] for col in inspector.get_columns('habit')]

            if 'why' not in habit_columns:
                print("[AUTO-MIGRATE] Adding 'why' column to habit table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text(
                            'ALTER TABLE habit ADD COLUMN why TEXT'
                        ))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully added 'why' column")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error adding 'why' column: {e}")

            # Migration 6: Add subscription fields to user table (combined from both versions)
            if 'user' in inspector.get_table_names():
                user_columns = [col['name'] for col in inspector.get_columns('user')]

                # Combined subscription field migrations from both versions
                # Use quoted table name "user" for PostgreSQL compatibility (user is a reserved word)
                subscription_migrations = [
                    ('subscription_tier', 'ALTER TABLE "user" ADD COLUMN subscription_tier VARCHAR(20) NOT NULL DEFAULT \'free\''),
                    ('subscription_status', 'ALTER TABLE "user" ADD COLUMN subscription_status VARCHAR(20) NOT NULL DEFAULT \'active\''),
                    ('subscription_start_date', 'ALTER TABLE "user" ADD COLUMN subscription_start_date TIMESTAMP'),
                    ('subscription_end_date', 'ALTER TABLE "user" ADD COLUMN subscription_end_date TIMESTAMP'),
                    ('trial_end_date', 'ALTER TABLE "user" ADD COLUMN trial_end_date TIMESTAMP'),
                    ('habit_limit', 'ALTER TABLE "user" ADD COLUMN habit_limit INTEGER NOT NULL DEFAULT 3'),
                    ('stripe_customer_id', 'ALTER TABLE "user" ADD COLUMN stripe_customer_id VARCHAR(255)'),
                    ('stripe_subscription_id', 'ALTER TABLE "user" ADD COLUMN stripe_subscription_id VARCHAR(255)'),
                    ('paypal_subscription_id', 'ALTER TABLE "user" ADD COLUMN paypal_subscription_id VARCHAR(255)'),
                    ('coinbase_charge_code', 'ALTER TABLE "user" ADD COLUMN coinbase_charge_code VARCHAR(255)'),
                    ('billing_email', 'ALTER TABLE "user" ADD COLUMN billing_email VARCHAR(120)'),
                    ('last_payment_date', 'ALTER TABLE "user" ADD COLUMN last_payment_date TIMESTAMP'),
                    ('payment_failures', 'ALTER TABLE "user" ADD COLUMN payment_failures INTEGER NOT NULL DEFAULT 0'),
                    ('email_notifications_enabled', 'ALTER TABLE "user" ADD COLUMN email_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE'),
                    ('reminder_time', 'ALTER TABLE "user" ADD COLUMN reminder_time VARCHAR(5) NOT NULL DEFAULT \'09:00\''),
                    ('reminder_days', 'ALTER TABLE "user" ADD COLUMN reminder_days VARCHAR(20) NOT NULL DEFAULT \'all\''),
                    ('last_reminder_sent', 'ALTER TABLE "user" ADD COLUMN last_reminder_sent DATE'),
                    ('account_deleted', 'ALTER TABLE "user" ADD COLUMN account_deleted BOOLEAN NOT NULL DEFAULT FALSE'),
                    ('deletion_scheduled_date', 'ALTER TABLE "user" ADD COLUMN deletion_scheduled_date TIMESTAMP'),
                ]

                for column_name, sql in subscription_migrations:
                    if column_name not in user_columns:
                        print(f"[AUTO-MIGRATE] Adding {column_name} to user table...")
                        try:
                            with db.engine.connect() as conn:
                                conn.execute(text(sql))
                                conn.commit()
                            print(f"[AUTO-MIGRATE] Successfully added {column_name}")
                        except Exception as e:
                            print(f"[AUTO-MIGRATE] Error adding {column_name}: {e}")

            # Migration 7: Create subscription_history table (LOCAL/HEAD version)
            existing_tables = inspector.get_table_names()

            if 'subscription_history' not in existing_tables:
                print("[AUTO-MIGRATE] Creating subscription_history table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text('''
                            CREATE TABLE subscription_history (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                subscription_type VARCHAR(20) NOT NULL,
                                status VARCHAR(20) NOT NULL,
                                started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                ended_at TIMESTAMP,
                                stripe_subscription_id VARCHAR(100),
                                amount DECIMAL(10, 2),
                                currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                                notes VARCHAR(500),
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES user (id)
                            )
                        '''))
                        conn.commit()

                        # Create indexes
                        conn.execute(text('CREATE INDEX idx_subscription_history_user_id ON subscription_history (user_id)'))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully created subscription_history table")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error creating subscription_history table: {e}")

            # Migration 8: Create payment_transaction table (LOCAL/HEAD version)
            if 'payment_transaction' not in existing_tables:
                print("[AUTO-MIGRATE] Creating payment_transaction table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text('''
                            CREATE TABLE payment_transaction (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                provider VARCHAR(20) NOT NULL DEFAULT 'stripe',
                                provider_transaction_id VARCHAR(100) NOT NULL UNIQUE,
                                stripe_invoice_id VARCHAR(100),
                                amount DECIMAL(10, 2) NOT NULL,
                                currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                                status VARCHAR(20) NOT NULL,
                                subscription_type VARCHAR(20) NOT NULL,
                                subscription_history_id INTEGER,
                                transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                payment_metadata TEXT,
                                FOREIGN KEY (user_id) REFERENCES user (id),
                                FOREIGN KEY (subscription_history_id) REFERENCES subscription_history (id)
                            )
                        '''))
                        conn.commit()

                        # Create indexes
                        conn.execute(text('CREATE INDEX idx_payment_transaction_user_id ON payment_transaction (user_id)'))
                        conn.execute(text('CREATE INDEX idx_payment_transaction_provider_id ON payment_transaction (provider_transaction_id)'))
                        conn.execute(text('CREATE INDEX idx_payment_transaction_date ON payment_transaction (transaction_date)'))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully created payment_transaction table")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error creating payment_transaction table: {e}")

            # Migration 9: Create subscription table (REMOTE version)
            if 'subscription' not in existing_tables:
                print("[AUTO-MIGRATE] Creating subscription table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text('''
                            CREATE TABLE subscription (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                tier VARCHAR(20) NOT NULL,
                                status VARCHAR(20) NOT NULL,
                                payment_provider VARCHAR(20) NOT NULL,
                                provider_subscription_id VARCHAR(255),
                                start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                end_date TIMESTAMP,
                                next_billing_date TIMESTAMP,
                                amount_paid REAL NOT NULL,
                                currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                                FOREIGN KEY (user_id) REFERENCES user (id)
                            )
                        '''))
                        conn.commit()

                        # Create indexes
                        conn.execute(text('CREATE INDEX idx_subscription_user_id ON subscription (user_id)'))
                        conn.execute(text('CREATE INDEX idx_subscription_status ON subscription (status)'))
                        conn.execute(text('CREATE INDEX idx_subscription_provider ON subscription (payment_provider)'))
                        conn.execute(text('CREATE INDEX idx_subscription_provider_id ON subscription (provider_subscription_id)'))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully created subscription table")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error creating subscription table: {e}")

            # Migration 10: Create payment table (REMOTE version)
            if 'payment' not in existing_tables:
                print("[AUTO-MIGRATE] Creating payment table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text('''
                            CREATE TABLE payment (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                subscription_id INTEGER,
                                payment_provider VARCHAR(20) NOT NULL,
                                provider_transaction_id VARCHAR(255) NOT NULL UNIQUE,
                                amount REAL NOT NULL,
                                currency VARCHAR(3) NOT NULL DEFAULT 'USD',
                                status VARCHAR(20) NOT NULL,
                                payment_type VARCHAR(20) NOT NULL,
                                payment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                notes TEXT,
                                FOREIGN KEY (user_id) REFERENCES user (id),
                                FOREIGN KEY (subscription_id) REFERENCES subscription (id)
                            )
                        '''))
                        conn.commit()

                        # Create indexes
                        conn.execute(text('CREATE INDEX idx_payment_user_id ON payment (user_id)'))
                        conn.execute(text('CREATE INDEX idx_payment_subscription_id ON payment (subscription_id)'))
                        conn.execute(text('CREATE INDEX idx_payment_provider ON payment (payment_provider)'))
                        conn.execute(text('CREATE INDEX idx_payment_transaction_id ON payment (provider_transaction_id)'))
                        conn.execute(text('CREATE INDEX idx_payment_status ON payment (status)'))
                        conn.execute(text('CREATE INDEX idx_payment_date ON payment (payment_date)'))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully created payment table")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error creating payment table: {e}")

            # Migration 11: Create period_cycle table
            if 'period_cycle' not in existing_tables:
                print("[AUTO-MIGRATE] Creating period_cycle table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text('''
                            CREATE TABLE period_cycle (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                start_date DATE NOT NULL,
                                end_date DATE,
                                cycle_length INTEGER,
                                is_predicted BOOLEAN NOT NULL DEFAULT 0,
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
                            )
                        '''))
                        conn.commit()

                        # Create indexes
                        conn.execute(text('CREATE INDEX idx_period_cycle_user_id ON period_cycle (user_id)'))
                        conn.execute(text('CREATE INDEX idx_period_cycle_start_date ON period_cycle (start_date)'))
                        conn.execute(text('CREATE INDEX idx_period_cycle_user_start ON period_cycle (user_id, start_date)'))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully created period_cycle table")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error creating period_cycle table: {e}")

            # Migration 12: Create period_daily_log table
            if 'period_daily_log' not in existing_tables:
                print("[AUTO-MIGRATE] Creating period_daily_log table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text('''
                            CREATE TABLE period_daily_log (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                cycle_id INTEGER,
                                user_id INTEGER NOT NULL,
                                log_date DATE NOT NULL,
                                flow_intensity VARCHAR(20),
                                symptoms TEXT,
                                mood VARCHAR(20),
                                notes TEXT,
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (cycle_id) REFERENCES period_cycle (id) ON DELETE CASCADE,
                                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                                UNIQUE (user_id, log_date)
                            )
                        '''))
                        conn.commit()

                        # Create indexes
                        conn.execute(text('CREATE INDEX idx_period_log_cycle_id ON period_daily_log (cycle_id)'))
                        conn.execute(text('CREATE INDEX idx_period_log_user_id ON period_daily_log (user_id)'))
                        conn.execute(text('CREATE INDEX idx_period_log_date ON period_daily_log (log_date)'))
                        conn.execute(text('CREATE INDEX idx_period_log_user_date ON period_daily_log (user_id, log_date)'))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully created period_daily_log table")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error creating period_daily_log table: {e}")

            # Migration 13: Create period_settings table
            if 'period_settings' not in existing_tables:
                print("[AUTO-MIGRATE] Creating period_settings table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text('''
                            CREATE TABLE period_settings (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL UNIQUE,
                                period_tracking_enabled BOOLEAN NOT NULL DEFAULT 0,
                                average_cycle_length INTEGER NOT NULL DEFAULT 28,
                                average_period_duration INTEGER NOT NULL DEFAULT 5,
                                reminder_enabled BOOLEAN NOT NULL DEFAULT 1,
                                reminder_days_before INTEGER NOT NULL DEFAULT 2,
                                last_reminder_sent DATE,
                                show_on_dashboard BOOLEAN NOT NULL DEFAULT 1,
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE
                            )
                        '''))
                        conn.commit()

                        # Create indexes
                        conn.execute(text('CREATE INDEX idx_period_settings_user_id ON period_settings (user_id)'))
                        conn.commit()

                    print("[AUTO-MIGRATE] Successfully created period_settings table")
                except Exception as e:
                    print(f"[AUTO-MIGRATE] Error creating period_settings table: {e}")

            print("[AUTO-MIGRATE] All migrations completed successfully")
        except Exception as e:
            print(f"[AUTO-MIGRATE] Error during migration check: {e}")
            # Don't crash the app if migration fails
            pass
