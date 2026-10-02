#!/usr/bin/env python3
"""
MuleTrace Deterministic Synthetic Dataset Generator
Generates realistic Indian banking transactions, KYC metadata, and evaluation ground truth.
Usage: python data/make_data.py --seed 42 --output-dir data/demo
"""

import argparse
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import pandas as pd

IST = timezone(timedelta(hours=5, minutes=30))

FIRST_NAMES = [
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Deepak", "Divya", "Gaurav",
    "Ishaan", "Kavya", "Manish", "Neha", "Nikhil", "Pooja", "Prateek", "Priya",
    "Rahul", "Riya", "Rohan", "Sanjay", "Shreya", "Siddharth", "Sneha", "Tanvi",
    "Varun", "Vikram", "Sunita", "Rajesh", "Kiran", "Meera", "Suresh", "Alok"
]
LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Singh", "Kumar", "Iyer", "Nair",
    "Reddy", "Rao", "Joshi", "Mehta", "Chopra", "Malhotra", "Bose", "Das",
    "Saxena", "Deshmukh", "Kulkarni", "Bhat", "Pandey", "Mishra", "Trivedi"
]


def make_hash(prefix: str, val: str) -> str:
    """Generate deterministic simulated hash for PII values."""
    h = hashlib.sha256(f"{prefix}:{val}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix.upper()}_{h}"


def generate_dataset(seed: int = 42, output_dir: Path = Path("data/demo")):
    """Generates synthetic accounts, transactions, and ground truth."""
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_time = datetime(2026, 9, 14, 0, 0, 0, tzinfo=IST)
    end_time = base_time + timedelta(days=14)

    accounts = []
    ground_truth = []
    transactions = []

    balances = {}  # account_id -> current balance

    # 1. Background Retail Accounts (~700 accounts)
    num_retail = 720
    for i in range(1, num_retail + 1):
        acc_id = f"ACC_RET_{i:04d}"
        fname = FIRST_NAMES[rng.integers(0, len(FIRST_NAMES))]
        lname = LAST_NAMES[rng.integers(0, len(LAST_NAMES))]
        name = f"{fname} {lname}"
        acc_type = "SAVINGS" if rng.random() > 0.15 else "CURRENT"
        
        # Opened between 6 months and 5 years prior to base_time
        age_days = int(rng.integers(180, 1800))
        opened_at = (base_time - timedelta(days=age_days)).strftime("%Y-%m-%d")
        
        kyc_verified = bool(rng.random() > 0.05)
        pan_hash = make_hash("pan", f"PAN_RET_{i}")
        phone_hash = make_hash("phn", f"98{rng.integers(10000000, 99999999)}")
        addr_hash = make_hash("addr", f"ADDR_RET_{i}")
        income = int(rng.choice([25000, 45000, 75000, 120000, 200000]))
        dev_id = f"DEV_MOB_{rng.integers(100000, 999999)}"
        ip_addr = f"49.36.{rng.integers(1, 255)}.{rng.integers(1, 255)}"
        
        initial_balance = float(rng.integers(5000, 150000))
        balances[acc_id] = initial_balance
        
        accounts.append({
            "account_id": acc_id,
            "display_name": name,
            "account_type": acc_type,
            "opened_at": opened_at,
            "kyc_verified": kyc_verified,
            "kyc_pan_hash": pan_hash,
            "kyc_phone_hash": phone_hash,
            "kyc_address_hash": addr_hash,
            "declared_monthly_income": income,
            "shared_network_tag": "RETAIL_POOL",
            "device_id": dev_id,
            "ip_address": ip_addr,
        })
        
        ground_truth.append({
            "account_id": acc_id,
            "label": "legit",
            "ring_id": "NONE",
            "ring_type": "none",
            "note": "Standard retail bank customer"
        })

    # 2. Hard Negatives (L1 - L8)
    # L1: Merchant Accounts (8)
    merchants = []
    for i in range(1, 9):
        acc_id = f"ACC_MERCHANT_{i:02d}"
        merchants.append(acc_id)
        name = f"QuickMart Store {i}" if i <= 4 else f"Bengaluru Fresh {i}"
        opened_at = (base_time - timedelta(days=int(rng.integers(800, 1500)))).strftime("%Y-%m-%d")
        balances[acc_id] = 50000.0
        accounts.append({
            "account_id": acc_id,
            "display_name": name,
            "account_type": "MERCHANT",
            "opened_at": opened_at,
            "kyc_verified": True,
            "kyc_pan_hash": make_hash("pan", f"MERCHANT_PAN_{i}"),
            "kyc_phone_hash": make_hash("phn", f"MERCHANT_PH_{i}"),
            "kyc_address_hash": make_hash("addr", f"MERCHANT_ADDR_{i}"),
            "declared_monthly_income": 800000,
            "shared_network_tag": "MERCHANT_GRID",
            "device_id": f"DEV_POS_{i:03d}",
            "ip_address": f"115.112.50.{10 + i}",
        })
        ground_truth.append({
            "account_id": acc_id,
            "label": "hard_negative",
            "ring_id": "RING_L1_MERCHANTS",
            "ring_type": "merchant",
            "note": "L1: Legitimate high-volume merchant with scheduled evening batch settlement"
        })

    # L2: Payroll Accounts (3 corporate accounts + payroll recipient pool)
    payrolls = []
    for i in range(1, 4):
        acc_id = f"ACC_PAYROLL_{i:02d}"
        payrolls.append(acc_id)
        name = f"Apex Tech Solutions Corp {i}"
        opened_at = (base_time - timedelta(days=1200)).strftime("%Y-%m-%d")
        balances[acc_id] = 5000000.0
        accounts.append({
            "account_id": acc_id,
            "display_name": name,
            "account_type": "CORPORATE",
            "opened_at": opened_at,
            "kyc_verified": True,
            "kyc_pan_hash": make_hash("pan", f"CORP_PAN_{i}"),
            "kyc_phone_hash": make_hash("phn", f"CORP_PH_{i}"),
            "kyc_address_hash": make_hash("addr", f"CORP_ADDR_{i}"),
            "declared_monthly_income": 10000000,
            "shared_network_tag": "CORP_NET",
            "device_id": f"DEV_CORP_{i:02d}",
            "ip_address": f"122.160.10.{i}",
        })
        ground_truth.append({
            "account_id": acc_id,
            "label": "hard_negative",
            "ring_id": "RING_L2_PAYROLL",
            "ring_type": "payroll",
            "note": "L2: Legitimate corporate payroll disbursement hub"
        })

    # L3: Wedding Gift Account
    acc_wedding = "ACC_WEDDING_01"
    balances[acc_wedding] = 12000.0
    accounts.append({
        "account_id": acc_wedding,
        "display_name": "Pooja & Rohan Wedding Fund",
        "account_type": "SAVINGS",
        "opened_at": (base_time - timedelta(days=400)).strftime("%Y-%m-%d"),
        "kyc_verified": True,
        "kyc_pan_hash": make_hash("pan", "WEDDING_PAN"),
        "kyc_phone_hash": make_hash("phn", "WEDDING_PH"),
        "kyc_address_hash": make_hash("addr", "WEDDING_ADDR"),
        "declared_monthly_income": 95000,
        "shared_network_tag": "RETAIL_POOL",
        "device_id": "DEV_WED_01",
        "ip_address": "49.36.100.12",
    })
    ground_truth.append({
        "account_id": acc_wedding,
        "label": "hard_negative",
        "ring_id": "RING_L3_WEDDING",
        "ring_type": "wedding",
        "note": "L3: Legitimate wedding gift aggregator (retains high balance, no rapid drain)"
    })

    # L4: Landlord Account
    acc_landlord = "ACC_LANDLORD_01"
    balances[acc_landlord] = 80000.0
    accounts.append({
        "account_id": acc_landlord,
        "display_name": "R. K. Sharma (Landlord)",
        "account_type": "SAVINGS",
        "opened_at": (base_time - timedelta(days=900)).strftime("%Y-%m-%d"),
        "kyc_verified": True,
        "kyc_pan_hash": make_hash("pan", "LANDLORD_PAN"),
        "kyc_phone_hash": make_hash("phn", "LANDLORD_PH"),
        "kyc_address_hash": make_hash("addr", "LANDLORD_ADDR"),
        "declared_monthly_income": 180000,
        "shared_network_tag": "RETAIL_POOL",
        "device_id": "DEV_LL_01",
        "ip_address": "49.36.120.45",
    })
    ground_truth.append({
        "account_id": acc_landlord,
        "label": "hard_negative",
        "ring_id": "RING_L4_LANDLORD",
        "ring_type": "landlord",
        "note": "L4: Legitimate rental collection account with multiple tenant deposits and no rapid drain"
    })

    # L5: Family Shared Device (4 accounts)
    fam_dev = "DEV_HOME_IPAD_01"
    for i in range(1, 5):
        acc_id = f"ACC_FAMILY_{i:02d}"
        balances[acc_id] = 40000.0
        accounts.append({
            "account_id": acc_id,
            "display_name": f"Verma Family Member {i}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=600 + i * 50)).strftime("%Y-%m-%d"),
            "kyc_verified": True,
            "kyc_pan_hash": make_hash("pan", f"FAM_PAN_{i}"),
            "kyc_phone_hash": make_hash("phn", f"FAM_PH_{i}"),
            "kyc_address_hash": make_hash("addr", "FAM_SHARED_ADDR"),
            "declared_monthly_income": 60000,
            "shared_network_tag": "FAMILY_HOME",
            "device_id": fam_dev,
            "ip_address": "106.51.72.88",
        })
        ground_truth.append({
            "account_id": acc_id,
            "label": "hard_negative",
            "ring_id": "RING_L5_FAMILY",
            "ring_type": "family",
            "note": "L5: Legitimate family accounts sharing a home tablet; long account tenure"
        })

    # L6: Friend Pairs (6 pairs = 12 accounts)
    for p in range(1, 7):
        acc_a = f"ACC_FRIEND_A{p}"
        acc_b = f"ACC_FRIEND_B{p}"
        for acc_id, side in [(acc_a, "A"), (acc_b, "B")]:
            balances[acc_id] = 35000.0
            accounts.append({
                "account_id": acc_id,
                "display_name": f"Friend {p}{side}",
                "account_type": "SAVINGS",
                "opened_at": (base_time - timedelta(days=365 + p * 20)).strftime("%Y-%m-%d"),
                "kyc_verified": True,
                "kyc_pan_hash": make_hash("pan", f"FRIEND_{p}_{side}"),
                "kyc_phone_hash": make_hash("phn", f"FRIEND_PH_{p}_{side}"),
                "kyc_address_hash": make_hash("addr", f"FRIEND_ADDR_{p}_{side}"),
                "declared_monthly_income": 50000,
                "shared_network_tag": "RETAIL_POOL",
                "device_id": f"DEV_FR_{p}_{side}",
                "ip_address": f"49.36.140.{p * 2 + (0 if side == 'A' else 1)}",
            })
            ground_truth.append({
                "account_id": acc_id,
                "label": "hard_negative",
                "ring_id": f"RING_L6_FRIEND_PAIR_{p}",
                "ring_type": "friend_pair",
                "note": f"L6: Legitimate peer-to-peer 2-party reimbursement cycle between friends"
            })

    # L7: Small Reseller Account
    acc_reseller = "ACC_RESELLER_01"
    balances[acc_reseller] = 45000.0
    accounts.append({
        "account_id": acc_reseller,
        "display_name": "CraftBazaar Reseller",
        "account_type": "CURRENT",
        "opened_at": (base_time - timedelta(days=1400)).strftime("%Y-%m-%d"),
        "kyc_verified": True,
        "kyc_pan_hash": make_hash("pan", "RESELLER_PAN"),
        "kyc_phone_hash": make_hash("phn", "RESELLER_PH"),
        "kyc_address_hash": make_hash("addr", "RESELLER_ADDR"),
        "declared_monthly_income": 120000,
        "shared_network_tag": "RESELLER_TAG",
        "device_id": "DEV_RESELL_01",
        "ip_address": "115.240.80.12",
    })
    ground_truth.append({
        "account_id": acc_reseller,
        "label": "hard_negative",
        "ring_id": "RING_L7_RESELLER",
        "ring_type": "reseller",
        "note": "L7: Legitimate small online reseller with multi-year tenure and steady inventory forwarding"
    })

    # L8: Campus Wi-Fi Shared IP (12 student accounts)
    campus_ip = "14.139.128.45"
    for i in range(1, 13):
        acc_id = f"ACC_STUDENT_{i:02d}"
        balances[acc_id] = 8000.0
        accounts.append({
            "account_id": acc_id,
            "display_name": f"Campus Student {i}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=400 + i * 15)).strftime("%Y-%m-%d"),
            "kyc_verified": True,
            "kyc_pan_hash": make_hash("pan", f"STUDENT_PAN_{i}"),
            "kyc_phone_hash": make_hash("phn", f"STUDENT_PH_{i}"),
            "kyc_address_hash": make_hash("addr", f"CAMPUS_HOSTEL_{i % 3}"),
            "declared_monthly_income": 15000,
            "shared_network_tag": "CAMPUS_WIFI",
            "device_id": f"DEV_STU_{i:02d}",
            "ip_address": campus_ip,
        })
        ground_truth.append({
            "account_id": acc_id,
            "label": "hard_negative",
            "ring_id": "RING_L8_CAMPUS",
            "ring_type": "campus_wifi",
            "note": "L8: Legitimate university students sharing campus Wi-Fi IP address; unique devices & PANs"
        })

    # 3. Fraud Rings (R1 to R6)
    # R1: Fan-In / Fan-Out Hub
    acc_mule_fan = "ACC_MULE_FAN01"
    acc_exit_crypto = "ACC_EXIT_CRYPTO"
    balances[acc_mule_fan] = 1500.0
    balances[acc_exit_crypto] = 10000.0
    accounts.append({
        "account_id": acc_mule_fan,
        "display_name": "Vikram S. Mule (Fan Hub)",
        "account_type": "SAVINGS",
        "opened_at": (base_time - timedelta(days=18)).strftime("%Y-%m-%d"),
        "kyc_verified": False,
        "kyc_pan_hash": make_hash("pan", "PAN_MULE_FAN"),
        "kyc_phone_hash": make_hash("phn", "PH_MULE_FAN"),
        "kyc_address_hash": make_hash("addr", "ADDR_MULE_FAN"),
        "declared_monthly_income": 20000,
        "shared_network_tag": "MULE_FAN_NET",
        "device_id": "DEV_MULE_FAN01",
        "ip_address": "103.21.244.11",
    })
    ground_truth.append({
        "account_id": acc_mule_fan,
        "label": "mule",
        "ring_id": "RING_R1_FAN_IN_OUT",
        "ring_type": "fan_in_out",
        "note": "R1: Rapid fan-in aggregation hub (₹4,05,000 received in 13 min, 96.3% forwarded)"
    })

    accounts.append({
        "account_id": acc_exit_crypto,
        "display_name": "CoinGateway Escrow Exit",
        "account_type": "CURRENT",
        "opened_at": (base_time - timedelta(days=65)).strftime("%Y-%m-%d"),
        "kyc_verified": True,
        "kyc_pan_hash": make_hash("pan", "PAN_EXIT_CRYPTO"),
        "kyc_phone_hash": make_hash("phn", "PH_EXIT_CRYPTO"),
        "kyc_address_hash": make_hash("addr", "ADDR_EXIT_CRYPTO"),
        "declared_monthly_income": 500000,
        "shared_network_tag": "CRYPTO_EXCHANGE",
        "device_id": "DEV_EXIT_CRYPTO",
        "ip_address": "103.21.244.99",
    })
    ground_truth.append({
        "account_id": acc_exit_crypto,
        "label": "exit",
        "ring_id": "RING_R1_FAN_IN_OUT",
        "ring_type": "fan_in_out",
        "note": "R1: Unregulated crypto OTC cash-out terminal exit"
    })

    fan_victims = []
    for v in range(1, 6):
        v_id = f"ACC_VICTIM_FAN{v:02d}"
        fan_victims.append(v_id)
        balances[v_id] = 120000.0
        accounts.append({
            "account_id": v_id,
            "display_name": f"Deceived Investor Victim {v}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=800 + v * 30)).strftime("%Y-%m-%d"),
            "kyc_verified": True,
            "kyc_pan_hash": make_hash("pan", f"PAN_VIC_FAN_{v}"),
            "kyc_phone_hash": make_hash("phn", f"PH_VIC_FAN_{v}"),
            "kyc_address_hash": make_hash("addr", f"ADDR_VIC_FAN_{v}"),
            "declared_monthly_income": 65000,
            "shared_network_tag": "RETAIL_POOL",
            "device_id": f"DEV_VIC_FAN_{v}",
            "ip_address": f"49.36.190.{v}",
        })
        ground_truth.append({
            "account_id": v_id,
            "label": "victim",
            "ring_id": "RING_R1_FAN_IN_OUT",
            "ring_type": "fan_in_out",
            "note": f"R1: Scam victim duped into transferring ₹81,000"
        })

    # R2: Pass-Through Layering Chain (Chain 01 -> 06 + Origin + Exit)
    chain_accounts = [f"ACC_CHAIN_{c:02d}" for c in range(1, 7)]
    acc_victim_chain = "ACC_VICTIM_CHAIN01"
    acc_exit_atm = "ACC_EXIT_ATM01"

    balances[acc_victim_chain] = 500000.0
    accounts.append({
        "account_id": acc_victim_chain,
        "display_name": "Dr. S. K. Verma (Phishing Victim)",
        "account_type": "SAVINGS",
        "opened_at": (base_time - timedelta(days=1500)).strftime("%Y-%m-%d"),
        "kyc_verified": True,
        "kyc_pan_hash": make_hash("pan", "PAN_VIC_CHAIN"),
        "kyc_phone_hash": make_hash("phn", "PH_VIC_CHAIN"),
        "kyc_address_hash": make_hash("addr", "ADDR_VIC_CHAIN"),
        "declared_monthly_income": 150000,
        "shared_network_tag": "RETAIL_POOL",
        "device_id": "DEV_VIC_CHAIN",
        "ip_address": "49.36.210.15",
    })
    ground_truth.append({
        "account_id": acc_victim_chain,
        "label": "victim",
        "ring_id": "RING_R2_PASSTHROUGH",
        "ring_type": "passthrough",
        "note": "R2: Cyber fraud victim whose funds enter multi-hop layering chain"
    })

    for c_idx, c_acc in enumerate(chain_accounts, start=1):
        balances[c_acc] = 200.0  # Starts with low balance
        accounts.append({
            "account_id": c_acc,
            "display_name": f"Layer Mule Node {c_idx:02d}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=12 + c_idx * 2)).strftime("%Y-%m-%d"),
            "kyc_verified": False,
            "kyc_pan_hash": make_hash("pan", f"PAN_CHAIN_{c_idx}"),
            "kyc_phone_hash": make_hash("phn", f"PH_CHAIN_{c_idx}"),
            "kyc_address_hash": make_hash("addr", f"ADDR_CHAIN_{c_idx}"),
            "declared_monthly_income": 15000,
            "shared_network_tag": "LAYER_CHAIN_NET",
            "device_id": f"DEV_CHAIN_{c_idx:02d}",
            "ip_address": f"103.88.190.{10 + c_idx}",
        })
        ground_truth.append({
            "account_id": c_acc,
            "label": "mule",
            "ring_id": "RING_R2_PASSTHROUGH",
            "ring_type": "passthrough",
            "note": f"R2: Hop #{c_idx} in rapid pass-through layering chain (forwards >97% in <3m)"
        })

    balances[acc_exit_atm] = 1000.0
    accounts.append({
        "account_id": acc_exit_atm,
        "display_name": "Metro Cash-Out Point Exit",
        "account_type": "SAVINGS",
        "opened_at": (base_time - timedelta(days=25)).strftime("%Y-%m-%d"),
        "kyc_verified": False,
        "kyc_pan_hash": make_hash("pan", "PAN_EXIT_ATM"),
        "kyc_phone_hash": make_hash("phn", "PH_EXIT_ATM"),
        "kyc_address_hash": make_hash("addr", "ADDR_EXIT_ATM"),
        "declared_monthly_income": 18000,
        "shared_network_tag": "ATM_CASH_OUT",
        "device_id": "DEV_EXIT_ATM",
        "ip_address": "103.88.190.99",
    })
    ground_truth.append({
        "account_id": acc_exit_atm,
        "label": "exit",
        "ring_id": "RING_R2_PASSTHROUGH",
        "ring_type": "passthrough",
        "note": "R2: Terminal ATM cash withdrawal card mule"
    })

    # R3: Circular Ring (Loop 01 -> 02 -> 03 -> 04 -> 01)
    loop_accounts = [f"ACC_LOOP_{l:02d}" for l in range(1, 5)]
    for l_idx, l_acc in enumerate(loop_accounts, start=1):
        balances[l_acc] = 105000.0 if l_idx == 1 else 5000.0
        accounts.append({
            "account_id": l_acc,
            "display_name": f"Circular Wash Mule {l_idx:02d}",
            "account_type": "CURRENT" if l_idx % 2 == 0 else "SAVINGS",
            "opened_at": (base_time - timedelta(days=22 + l_idx * 3)).strftime("%Y-%m-%d"),
            "kyc_verified": bool(l_idx % 2 == 0),
            "kyc_pan_hash": make_hash("pan", f"PAN_LOOP_{l_idx}"),
            "kyc_phone_hash": make_hash("phn", f"PH_LOOP_{l_idx}"),
            "kyc_address_hash": make_hash("addr", f"ADDR_LOOP_{l_idx}"),
            "declared_monthly_income": 35000,
            "shared_network_tag": "LOOP_NET",
            "device_id": f"DEV_LOOP_{l_idx:02d}",
            "ip_address": f"103.111.45.{l_idx}",
        })
        ground_truth.append({
            "account_id": l_acc,
            "label": "mule",
            "ring_id": "RING_R3_CIRCULAR",
            "ring_type": "cycle",
            "note": f"R3: Member of 4-hop wash trading cycle (₹95,000 loop in 38m)"
        })

    # R4: Sybil Ring (4 accounts sharing device DEV_EMU_9901, PANH_SYBIL_01, IP 103.88.201.99, opened 2 days prior)
    sybil_dev = "DEV_EMU_9901"
    sybil_pan = make_hash("pan", "PANH_SYBIL_01")
    sybil_ip = "103.88.201.99"
    sybil_accounts = [f"ACC_SYBIL_{s:02d}" for s in range(1, 5)]
    for s_idx, s_acc in enumerate(sybil_accounts, start=1):
        balances[s_acc] = 2000.0
        accounts.append({
            "account_id": s_acc,
            "display_name": f"Sybil Synthetic Identity {s_idx:02d}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=2)).strftime("%Y-%m-%d"),
            "kyc_verified": False,
            "kyc_pan_hash": sybil_pan,
            "kyc_phone_hash": make_hash("phn", f"SYBIL_PH_{s_idx}"),
            "kyc_address_hash": make_hash("addr", "SYBIL_GHOST_FLAT"),
            "declared_monthly_income": 22000,
            "shared_network_tag": "SYBIL_FARM",
            "device_id": sybil_dev,
            "ip_address": sybil_ip,
        })
        ground_truth.append({
            "account_id": s_acc,
            "label": "mule",
            "ring_id": "RING_R4_SYBIL",
            "ring_type": "sybil",
            "note": "R4: Sybil cluster account sharing hardware device, forged PAN, and IP address"
        })

    # R5: Full Scam Story (Victim -> 1 Layer 1 -> 3 Layer 2 -> 6 Layer 3 -> 3 Exits)
    acc_story_victim = "ACC_VICTIM_01"
    balances[acc_story_victim] = 300000.0
    accounts.append({
        "account_id": acc_story_victim,
        "display_name": "Meera Ramanathan (Retiree Victim)",
        "account_type": "SAVINGS",
        "opened_at": (base_time - timedelta(days=2400)).strftime("%Y-%m-%d"),
        "kyc_verified": True,
        "kyc_pan_hash": make_hash("pan", "PAN_STORY_VIC"),
        "kyc_phone_hash": make_hash("phn", "PH_STORY_VIC"),
        "kyc_address_hash": make_hash("addr", "ADDR_STORY_VIC"),
        "declared_monthly_income": 70000,
        "shared_network_tag": "RETAIL_POOL",
        "device_id": "DEV_VIC_STORY_01",
        "ip_address": "49.36.180.20",
    })
    ground_truth.append({
        "account_id": acc_story_victim,
        "label": "victim",
        "ring_id": "RING_R5_SCAM_STORY",
        "ring_type": "story",
        "note": "R5: Senior citizen victim defrauded of ₹2,40,000 in digital arrest scam"
    })

    acc_story_l1 = "ACC_STORY_L1_01"
    balances[acc_story_l1] = 500.0
    accounts.append({
        "account_id": acc_story_l1,
        "display_name": "Karan Malhotra (Primary Mule Ingestion)",
        "account_type": "SAVINGS",
        "opened_at": (base_time - timedelta(days=14)).strftime("%Y-%m-%d"),
        "kyc_verified": False,
        "kyc_pan_hash": make_hash("pan", "PAN_STORY_L1"),
        "kyc_phone_hash": make_hash("phn", "PH_STORY_L1"),
        "kyc_address_hash": make_hash("addr", "ADDR_STORY_L1"),
        "declared_monthly_income": 18000,
        "shared_network_tag": "STORY_RING_NET",
        "device_id": "DEV_STORY_L1",
        "ip_address": "103.88.220.10",
    })
    ground_truth.append({
        "account_id": acc_story_l1,
        "label": "mule",
        "ring_id": "RING_R5_SCAM_STORY",
        "ring_type": "story",
        "note": "R5: Primary ingestion mule receiving direct victim transfer"
    })

    story_l2_accounts = [f"ACC_STORY_L2_{i:02d}" for i in range(1, 4)]
    for i, a_id in enumerate(story_l2_accounts, start=1):
        balances[a_id] = 400.0
        accounts.append({
            "account_id": a_id,
            "display_name": f"Layer 2 Relay Mule {i:02d}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=15 + i)).strftime("%Y-%m-%d"),
            "kyc_verified": False,
            "kyc_pan_hash": make_hash("pan", f"PAN_STORY_L2_{i}"),
            "kyc_phone_hash": make_hash("phn", f"PH_STORY_L2_{i}"),
            "kyc_address_hash": make_hash("addr", f"ADDR_STORY_L2_{i}"),
            "declared_monthly_income": 20000,
            "shared_network_tag": "STORY_RING_NET",
            "device_id": f"DEV_STORY_L2_{i:02d}",
            "ip_address": f"103.88.220.{20 + i}",
        })
        ground_truth.append({
            "account_id": a_id,
            "label": "mule",
            "ring_id": "RING_R5_SCAM_STORY",
            "ring_type": "story",
            "note": f"R5: Intermediate fan-out dispersal mule {i}"
        })

    story_l3_accounts = [f"ACC_STORY_L3_{i:02d}" for i in range(1, 7)]
    for i, a_id in enumerate(story_l3_accounts, start=1):
        balances[a_id] = 300.0
        accounts.append({
            "account_id": a_id,
            "display_name": f"Layer 3 Smurfing Node {i:02d}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=10 + i)).strftime("%Y-%m-%d"),
            "kyc_verified": False,
            "kyc_pan_hash": make_hash("pan", f"PAN_STORY_L3_{i}"),
            "kyc_phone_hash": make_hash("phn", f"PH_STORY_L3_{i}"),
            "kyc_address_hash": make_hash("addr", f"ADDR_STORY_L3_{i}"),
            "declared_monthly_income": 20000,
            "shared_network_tag": "STORY_RING_NET",
            "device_id": f"DEV_STORY_L3_{i:02d}",
            "ip_address": f"103.88.220.{30 + i}",
        })
        ground_truth.append({
            "account_id": a_id,
            "label": "mule",
            "ring_id": "RING_R5_SCAM_STORY",
            "ring_type": "story",
            "note": f"R5: Micro-layer smurfing mule {i}"
        })

    story_exit_accounts = [f"ACC_STORY_EXIT_{i:02d}" for i in range(1, 4)]
    for i, a_id in enumerate(story_exit_accounts, start=1):
        balances[a_id] = 1000.0
        accounts.append({
            "account_id": a_id,
            "display_name": f"Terminal Extraction Channel {i:02d}",
            "account_type": "CURRENT",
            "opened_at": (base_time - timedelta(days=40)).strftime("%Y-%m-%d"),
            "kyc_verified": True,
            "kyc_pan_hash": make_hash("pan", f"PAN_STORY_EX_{i}"),
            "kyc_phone_hash": make_hash("phn", f"PH_STORY_EX_{i}"),
            "kyc_address_hash": make_hash("addr", f"ADDR_STORY_EX_{i}"),
            "declared_monthly_income": 400000,
            "shared_network_tag": "EXTRACTION_TERMINAL",
            "device_id": f"DEV_STORY_EX_{i:02d}",
            "ip_address": f"103.88.220.{90 + i}",
        })
        ground_truth.append({
            "account_id": a_id,
            "label": "exit",
            "ring_id": "RING_R5_SCAM_STORY",
            "ring_type": "story",
            "note": f"R5: Final cash extraction point {i}"
        })

    # R6: Evasion Test Ring (Slow-paced transfers: 7 inflows over 55m, 50m pause, small outbounds)
    acc_evasion_hub = "ACC_EVASION_HUB01"
    balances[acc_evasion_hub] = 1200.0
    accounts.append({
        "account_id": acc_evasion_hub,
        "display_name": "Low-Velocity Concealed Hub",
        "account_type": "SAVINGS",
        "opened_at": (base_time - timedelta(days=38)).strftime("%Y-%m-%d"),
        "kyc_verified": True,
        "kyc_pan_hash": make_hash("pan", "PAN_EVASION_HUB"),
        "kyc_phone_hash": make_hash("phn", "PH_EVASION_HUB"),
        "kyc_address_hash": make_hash("addr", "ADDR_EVASION_HUB"),
        "declared_monthly_income": 45000,
        "shared_network_tag": "EVASION_POOL",
        "device_id": "DEV_EVASION_01",
        "ip_address": "103.95.80.12",
    })
    ground_truth.append({
        "account_id": acc_evasion_hub,
        "label": "mule",
        "ring_id": "RING_R6_EVASION",
        "ring_type": "evasion",
        "note": "R6: Evasion ring hub configured to be caught under relaxed settings, but evasive under balanced/strict"
    })

    evasion_senders = [f"ACC_EVASION_SRC_{i:02d}" for i in range(1, 8)]
    for i, a_id in enumerate(evasion_senders, start=1):
        balances[a_id] = 50000.0
        accounts.append({
            "account_id": a_id,
            "display_name": f"Evasion Source {i:02d}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=200 + i * 10)).strftime("%Y-%m-%d"),
            "kyc_verified": True,
            "kyc_pan_hash": make_hash("pan", f"PAN_EV_SRC_{i}"),
            "kyc_phone_hash": make_hash("phn", f"PH_EV_SRC_{i}"),
            "kyc_address_hash": make_hash("addr", f"ADDR_EV_SRC_{i}"),
            "declared_monthly_income": 35000,
            "shared_network_tag": "RETAIL_POOL",
            "device_id": f"DEV_EV_SRC_{i:02d}",
            "ip_address": f"49.36.230.{i}",
        })
        ground_truth.append({
            "account_id": a_id,
            "label": "victim",
            "ring_id": "RING_R6_EVASION",
            "ring_type": "evasion",
            "note": f"R6: Inflow source {i} for evasion test"
        })

    evasion_exits = [f"ACC_EVASION_EX_{i:02d}" for i in range(1, 4)]
    for i, a_id in enumerate(evasion_exits, start=1):
        balances[a_id] = 5000.0
        accounts.append({
            "account_id": a_id,
            "display_name": f"Evasion Exit {i:02d}",
            "account_type": "SAVINGS",
            "opened_at": (base_time - timedelta(days=50 + i * 5)).strftime("%Y-%m-%d"),
            "kyc_verified": True,
            "kyc_pan_hash": make_hash("pan", f"PAN_EV_EX_{i}"),
            "kyc_phone_hash": make_hash("phn", f"PH_EV_EX_{i}"),
            "kyc_address_hash": make_hash("addr", f"ADDR_EV_EX_{i}"),
            "declared_monthly_income": 50000,
            "shared_network_tag": "EVASION_POOL",
            "device_id": f"DEV_EV_EX_{i:02d}",
            "ip_address": f"103.95.80.{50 + i}",
        })
        ground_truth.append({
            "account_id": a_id,
            "label": "exit",
            "ring_id": "RING_R6_EVASION",
            "ring_type": "evasion",
            "note": f"R6: Exit destination {i} for evasion test"
        })

    # Record all account metadata
    account_lookup = {acc["account_id"]: acc for acc in accounts}
    txn_counter = 1

    def add_txn(ts: datetime, src: str, dst: str, amt: float, channel: str = "UPI"):
        nonlocal txn_counter
        src_bal_before = balances[src]
        dst_bal_before = balances[dst]
        
        src_bal_after = round(src_bal_before - amt, 2)
        dst_bal_after = round(dst_bal_before + amt, 2)
        
        balances[src] = src_bal_after
        balances[dst] = dst_bal_after
        
        dev = account_lookup[src]["device_id"]
        ip = account_lookup[src]["ip_address"]
        
        transactions.append({
            "txn_id": f"TXN_{txn_counter:07d}",
            "timestamp": ts.isoformat(),
            "source_account": src,
            "dest_account": dst,
            "amount": amt,
            "channel": channel,
            "device_id": dev,
            "ip_address": ip,
            "source_balance_after": src_bal_after,
            "dest_balance_after": dst_bal_after,
        })
        txn_counter += 1

    # 4. Generate Planted Fraud Transactions
    print("Injecting planted fraud ring transactions...")

    # R1: Fan-In / Fan-Out Hub
    # Starts on Day 2: 2026-09-15 14:10:00 IST
    t_r1 = base_time + timedelta(days=1, hours=14, minutes=10)
    # 5 victims send ₹81,000 each over 13 minutes (Total = ₹4,05,000)
    for i, v_acc in enumerate(fan_victims):
        ts_vic = t_r1 + timedelta(minutes=int(i * 2.5))
        add_txn(ts_vic, v_acc, acc_mule_fan, 81000.0, "UPI")
    
    # 5 minutes after last inflow, forwards ₹3,90,000 (96.3% forward ratio) to ACC_EXIT_CRYPTO
    ts_r1_out = t_r1 + timedelta(minutes=18)
    add_txn(ts_r1_out, acc_mule_fan, acc_exit_crypto, 390000.0, "IMPS")

    # R2: Pass-Through Layering Chain
    # Starts on Day 3: 2026-09-16 11:00:00 IST
    t_r2 = base_time + timedelta(days=2, hours=11, minutes=0)
    # Victim sends ₹3,50,000 to Chain_01
    add_txn(t_r2, acc_victim_chain, chain_accounts[0], 350000.0, "NEFT")
    
    # Each chain node forwards within 1-3 minutes, ending below ₹400 balance
    curr_amt = 350000.0
    curr_time = t_r2
    for c_idx in range(len(chain_accounts) - 1):
        curr_time = curr_time + timedelta(minutes=2)
        deduction = float(rng.integers(80, 150))
        forward_amt = round(curr_amt - deduction, 2)
        add_txn(curr_time, chain_accounts[c_idx], chain_accounts[c_idx + 1], forward_amt, "IMPS")
        curr_amt = forward_amt
    
    # Final chain node forwards to ATM exit
    curr_time = curr_time + timedelta(minutes=2)
    final_amt = round(curr_amt - 100.0, 2)
    add_txn(curr_time, chain_accounts[-1], acc_exit_atm, final_amt, "IMPS")

    # R3: Circular Transfer Ring
    # Starts on Day 4: 2026-09-17 16:00:00 IST
    t_r3 = base_time + timedelta(days=3, hours=16, minutes=0)
    # ₹95,000 loop in ~38 minutes (01 -> 02 -> 03 -> 04 -> 01)
    # Hop 1: 01 -> 02, ₹95,000
    add_txn(t_r3, loop_accounts[0], loop_accounts[1], 95000.0, "UPI")
    # Hop 2: 02 -> 03, ₹93,000 (+9 min)
    add_txn(t_r3 + timedelta(minutes=9), loop_accounts[1], loop_accounts[2], 93000.0, "UPI")
    # Hop 3: 03 -> 04, ₹91,000 (+19 min) (contains 17% deviation test from starting: 95000 -> ~79000, here 85000)
    add_txn(t_r3 + timedelta(minutes=19), loop_accounts[2], loop_accounts[3], 85000.0, "IMPS")
    # Hop 4: 04 -> 01, ₹83,000 (+38 min) (total duration 38 mins)
    add_txn(t_r3 + timedelta(minutes=38), loop_accounts[3], loop_accounts[0], 83000.0, "UPI")

    # R4: Sybil Transfers
    # Day 5: Transfers between sybils and external exit
    t_r4 = base_time + timedelta(days=4, hours=13, minutes=0)
    for s_idx in range(len(sybil_accounts) - 1):
        add_txn(t_r4 + timedelta(minutes=s_idx * 5), sybil_accounts[s_idx], sybil_accounts[s_idx + 1], 1500.0, "UPI")

    # R5: Full Scam Story
    # Day 6: 2026-09-19 10:00:00 IST
    t_r5 = base_time + timedelta(days=5, hours=10, minutes=0)
    # Victim sends ₹2,40,000 to Layer 1 Hub
    add_txn(t_r5, acc_story_victim, acc_story_l1, 240000.0, "IMPS")
    
    # Layer 1 disperses to 3 Layer 2 accounts (+5m): ₹78,000 each (Total ₹2,34,000 = 97.5%)
    t_l2 = t_r5 + timedelta(minutes=5)
    for idx, l2_acc in enumerate(story_l2_accounts):
        add_txn(t_l2 + timedelta(minutes=idx), acc_story_l1, l2_acc, 78000.0, "IMPS")
        
        # Each Layer 2 disperses to 2 Layer 3 accounts (+8m): ₹38,000 each (Total ₹76,000 per L2 = 97.4%)
        t_l3 = t_l2 + timedelta(minutes=8)
        target_l3 = story_l3_accounts[idx * 2 : (idx + 1) * 2]
        for jdx, l3_acc in enumerate(target_l3):
            add_txn(t_l3 + timedelta(minutes=jdx), l2_acc, l3_acc, 38000.0, "UPI")
            
            # Each Layer 3 sends to an Exit account (+10m): ₹37,000
            t_ex = t_l3 + timedelta(minutes=10)
            ex_target = story_exit_accounts[(idx * 2 + jdx) % len(story_exit_accounts)]
            add_txn(t_ex, l3_acc, ex_target, 37000.0, "UPI")

    # R6: Evasion Ring (7 small inflows over 55 mins, 50m pause, small outbounds)
    # Day 7: 2026-09-20 09:00:00 IST
    t_r6 = base_time + timedelta(days=6, hours=9, minutes=0)
    # 7 inflows of ₹7,500 over 55 mins (total ₹52,500)
    for i, src in enumerate(evasion_senders):
        ts_in = t_r6 + timedelta(minutes=int(i * 8.5))
        add_txn(ts_in, src, acc_evasion_hub, 7500.0, "UPI")
    
    # 50 min pause, then 3 outbound transfers of ₹16,500 (total ₹49,500 = 94.2%)
    t_r6_out = t_r6 + timedelta(minutes=55 + 50)
    for i, ex in enumerate(evasion_exits):
        ts_out = t_r6_out + timedelta(minutes=i * 5)
        add_txn(ts_out, acc_evasion_hub, ex, 16500.0, "UPI")

    # 5. Generate Legitimate Patterns (Hard Negatives Activity)
    print("Generating legitimate hard negative activity...")

    # L1: Merchant Accounts: regular daytime purchases, single evening settlement
    for d in range(14):
        day_date = base_time + timedelta(days=d)
        for m_acc in merchants:
            # 15 to 30 customer payments between 09:00 and 21:00
            n_payments = int(rng.integers(15, 30))
            day_total = 0.0
            for _ in range(n_payments):
                cust = f"ACC_RET_{rng.integers(1, num_retail + 1):04d}"
                hr = int(rng.integers(9, 21))
                mn = int(rng.integers(0, 60))
                amt = float(rng.integers(150, 2500))
                day_total += amt
                add_txn(day_date + timedelta(hours=hr, minutes=mn), cust, m_acc, amt, "UPI")
            
            # Evening settlement payout to merchant master at 23:15
            settle_amt = round(day_total * 0.90, 2)
            master_acc = f"ACC_RET_{rng.integers(1, 100):04d}"
            add_txn(day_date + timedelta(hours=23, minutes=15), m_acc, master_acc, settle_amt, "IMPS")

    # L2: Payroll Accounts: 1 large monthly or bi-weekly disbursement to 35 employee accounts
    for p_acc in payrolls:
        t_payroll = base_time + timedelta(days=3, hours=10, minutes=0)
        for emp_idx in range(1, 36):
            emp_acc = f"ACC_RET_{emp_idx + 100:04d}"
            salary = float(rng.choice([35000, 52000, 68000, 85000, 110000]))
            add_txn(t_payroll + timedelta(minutes=emp_idx), p_acc, emp_acc, salary, "NEFT")

    # L3: Wedding Gifts: 25 gifts received over 2 days, money kept
    t_wed = base_time + timedelta(days=4, hours=11, minutes=0)
    for g in range(1, 26):
        gift_giver = f"ACC_RET_{rng.integers(1, num_retail + 1):04d}"
        gift_amt = float(rng.choice([2100, 5100, 11000, 21000]))
        ts_gift = t_wed + timedelta(hours=int(g * 1.5), minutes=int(rng.integers(1, 50)))
        add_txn(ts_gift, gift_giver, acc_wedding, gift_amt, "UPI")

    # L4: Landlord: 6 tenant rent payments on 1st of month (base_time + 1 day)
    t_rent = base_time + timedelta(days=1, hours=8, minutes=0)
    for tn in range(1, 7):
        tenant = f"ACC_RET_{tn + 250:04d}"
        rent_amt = float(rng.choice([18000, 22000, 26000]))
        add_txn(t_rent + timedelta(hours=tn * 2), tenant, acc_landlord, rent_amt, "UPI")

    # L5: Family Shared Device: intermittent domestic transfers
    fam_accounts = [f"ACC_FAMILY_{i:02d}" for i in range(1, 5)]
    for d in range(1, 10, 2):
        t_fam = base_time + timedelta(days=d, hours=19, minutes=0)
        add_txn(t_fam, fam_accounts[0], fam_accounts[1], 3500.0, "UPI")
        add_txn(t_fam + timedelta(hours=2), fam_accounts[2], fam_accounts[3], 1200.0, "UPI")

    # L6: Friend Pairs: back and forth peer transfers
    for p in range(1, 7):
        acc_a = f"ACC_FRIEND_A{p}"
        acc_b = f"ACC_FRIEND_B{p}"
        for d in [1, 4, 7, 11]:
            t_fr = base_time + timedelta(days=d, hours=13, minutes=int(p * 5))
            add_txn(t_fr, acc_a, acc_b, 1500.0, "UPI")
            add_txn(t_fr + timedelta(days=1, hours=4), acc_b, acc_a, 1500.0, "UPI")

    # L7: Small Reseller: receives from ~6 customers, forwards ~85% in ~40m, 4 years old, KYC verified
    t_resell = base_time + timedelta(days=5, hours=14, minutes=0)
    total_resell = 0.0
    for c_i in range(1, 7):
        cust = f"ACC_RET_{c_i + 300:04d}"
        amt = float(rng.integers(1200, 4500))
        total_resell += amt
        add_txn(t_resell + timedelta(minutes=c_i * 3), cust, acc_reseller, amt, "UPI")
    # Forwards 85% after 42 minutes
    add_txn(t_resell + timedelta(minutes=42), acc_reseller, f"ACC_RET_{num_retail:04d}", round(total_resell * 0.85, 2), "IMPS")

    # L8: Campus Wi-Fi Students: occasional canteen & bill splits
    student_accounts = [f"ACC_STUDENT_{i:02d}" for i in range(1, 13)]
    for d in range(1, 12, 3):
        t_stu = base_time + timedelta(days=d, hours=12, minutes=30)
        for s_i in range(len(student_accounts) - 1):
            add_txn(t_stu + timedelta(minutes=s_i * 4), student_accounts[s_i], student_accounts[s_i + 1], 150.0, "UPI")

    # 6. Generate Realistic Background Noise Transactions (~7,000 - 8,500)
    print("Generating background retail transactions...")
    target_bg_count = 7500
    for _ in range(target_bg_count):
        # Pick random day and time
        sec_offset = rng.integers(0, 14 * 24 * 3600)
        txn_ts = base_time + timedelta(seconds=int(sec_offset))
        
        # Pick 2 distinct retail accounts
        src_idx = int(rng.integers(1, num_retail + 1))
        dst_idx = int(rng.integers(1, num_retail + 1))
        while dst_idx == src_idx:
            dst_idx = int(rng.integers(1, num_retail + 1))
            
        src = f"ACC_RET_{src_idx:04d}"
        dst = f"ACC_RET_{dst_idx:04d}"
        
        # Realistic retail amount (power law / lognormal, ₹50 to ₹18,000)
        amt = float(round(rng.lognormal(mean=6.5, sigma=1.2), 2))
        amt = max(50.0, min(amt, 18000.0))
        
        # Ensure sender has enough balance
        if balances[src] <= amt + 500:
            balances[src] += amt + 15000.0  # simulate prior income
            
        channel = rng.choice(["UPI", "IMPS", "NEFT"], p=[0.80, 0.15, 0.05])
        add_txn(txn_ts, src, dst, amt, channel)

    # 7. Sort Transactions Chronologically
    print("Sorting transactions chronologically and building DataFrames...")
    df_txns = pd.DataFrame(transactions)
    df_txns["timestamp_dt"] = pd.to_datetime(df_txns["timestamp"])
    df_txns = df_txns.sort_values("timestamp_dt").reset_index(drop=True)
    df_txns = df_txns.drop(columns=["timestamp_dt"])
    
    # Re-index txn_id cleanly
    df_txns["txn_id"] = [f"TXN_{i:07d}" for i in range(1, len(df_txns) + 1)]

    df_accounts = pd.DataFrame(accounts).sort_values("account_id").reset_index(drop=True)
    df_ground_truth = pd.DataFrame(ground_truth).sort_values("account_id").reset_index(drop=True)

    # Save to CSV
    txns_path = output_dir / "transactions.csv"
    accs_path = output_dir / "accounts.csv"
    gt_path = output_dir / "ground_truth.csv"

    df_txns.to_csv(txns_path, index=False)
    df_accounts.to_csv(accs_path, index=False)
    df_ground_truth.to_csv(gt_path, index=False)

    print(f"[OK] Generated {len(df_accounts)} accounts.")
    print(f"[OK] Generated {len(df_txns)} transactions ({df_txns['channel'].value_counts().to_dict()}).")
    print(f"[OK] Generated {len(df_ground_truth)} ground truth labels.")
    print(f"[OK] Files written to {output_dir}")

    return df_txns, df_accounts, df_ground_truth


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MuleTrace Synthetic Dataset Generator")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    parser.add_argument("--output-dir", type=str, default="data/demo", help="Target output folder")
    args = parser.parse_args()

    generate_dataset(seed=args.seed, output_dir=Path(args.output_dir))
