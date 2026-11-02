"""
Realistic Synthetic Data Seeder for Monitored Application Database.
Produces clean, deterministic, multi-tenant relational business records.
"""
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from faker import Faker
from sqlalchemy.orm import Session
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.models.order import Order, OrderItem
from backend.app.models.audit_log import AuditLog
from backend.app.core.logging import logger

fake = Faker()
Faker.seed(42)  # Deterministic seed for reproducible tests


def seed_synthetic_database(
    session: Session,
    num_orgs: int = 3,
    users_per_org: int = 5,
    orders_per_user: int = 4
) -> Dict[str, int]:
    """
    Populates the database with realistic synthetic business records.
    Returns a dictionary of generated counts per table.
    """
    logger.info("Starting synthetic database population...")
    counts = {
        "organizations": 0,
        "users": 0,
        "orders": 0,
        "order_items": 0,
        "audit_logs": 0
    }

    tiers = ["ENTERPRISE", "PRO", "SCALE"]
    roles = ["ADMIN", "DEVOPS", "SECURITY_ENGINEER", "FINANCE_ANALYST", "DEVELOPER"]
    skus = [
        ("AWS-ECS-COMPUTE", "Elastic Container Service Compute Node", 4500),
        ("AWS-RDS-PGSQL", "Amazon RDS PostgreSQL Multi-AZ Instance", 12500),
        ("AWS-S3-GLACIER", "S3 Glacier Deep Archive Storage 1TB", 100),
        ("CG-DR-AUDITOR", "CloudGuard DR Realtime Health Sensor", 2500),
        ("CG-BACKUP-ENCRYPT", "Disaster Recovery KMS Encryption Key", 1000)
    ]

    for i in range(num_orgs):
        org_name = f"{fake.company()} {fake.company_suffix()}"
        slug = f"org-{uuid.uuid4().hex[:8]}"
        org = Organization(
            id=str(uuid.uuid4()),
            name=org_name,
            slug=slug,
            tier=tiers[i % len(tiers)],
            is_active=True
        )
        session.add(org)
        counts["organizations"] += 1

        # Audit log for org creation
        session.add(AuditLog(
            id=str(uuid.uuid4()),
            actor_email="system-provisioner@cloudguard.internal",
            action="ORGANIZATION_INITIALIZED",
            resource_type="organization",
            resource_id=org.id,
            details=f"Initialized tenant organization {org.name}",
            ip_address="10.0.4.12"
        ))
        counts["audit_logs"] += 1

        for u_idx in range(users_per_org):
            full_name = fake.name()
            email = f"{full_name.lower().replace(' ', '.')}_{uuid.uuid4().hex[:4]}@{slug}.cloud"
            pwd_hash = hashlib.sha256(f"SecretPwd-{email}".encode()).hexdigest()
            user = User(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                email=email,
                full_name=full_name,
                role=roles[u_idx % len(roles)],
                password_hash=pwd_hash
            )
            session.add(user)
            counts["users"] += 1

            for o_idx in range(orders_per_user):
                order_num = f"ORD-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:8].upper()}"
                order = Order(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    user_id=user.id,
                    order_number=order_num,
                    status="COMPLETED",
                    currency="USD",
                    total_amount_cents=0
                )
                session.add(order)
                counts["orders"] += 1

                # Generate 2 items per order
                order_total = 0
                for item_idx in range(2):
                    sku_choice = skus[(u_idx + o_idx + item_idx) % len(skus)]
                    qty = (item_idx % 3) + 1
                    item_total = sku_choice[2] * qty
                    order_total += item_total

                    item = OrderItem(
                        id=str(uuid.uuid4()),
                        order_id=order.id,
                        sku=sku_choice[0],
                        name=sku_choice[1],
                        unit_price_cents=sku_choice[2],
                        quantity=qty
                    )
                    session.add(item)
                    counts["order_items"] += 1

                order.total_amount_cents = order_total

                # Audit entry for order placement
                session.add(AuditLog(
                    id=str(uuid.uuid4()),
                    actor_email=user.email,
                    action="TRANSACTION_COMMITTED",
                    resource_type="order",
                    resource_id=order.id,
                    details=f"Order {order_num} committed for {order_total} cents",
                    ip_address="192.168.1.105"
                ))
                counts["audit_logs"] += 1

    session.commit()
    logger.info(f"Synthetic database populated successfully: {counts}")
    return counts
