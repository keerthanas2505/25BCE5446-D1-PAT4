-- ============================================================================
-- HOSPITAL PHARMACY MANAGEMENT SYSTEM (HPMS)
-- Sample Seed Data Script (seed_data.sql)
-- Oracle Database XE 21c (Pluggable Database: XEPDB1)
-- VIT Chennai DBMS PAT 4 Project
-- ============================================================================
-- NOTE: This script is fully IDEMPOTENT. Executing it multiple times will NOT
-- create duplicate records or fail unique constraints.
-- All data contained herein consists strictly of FICTIONAL DEMONSTRATION RECORDS
-- for academic laboratory presentation only.
-- ============================================================================

SET DEFINE OFF;
SET SERVEROUTPUT ON;

-- ----------------------------------------------------------------------------
-- 1. SEED SUPPLIERS
-- ----------------------------------------------------------------------------
DECLARE
    v_cnt NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_cnt FROM SUPPLIER WHERE supplier_name = 'MedPlus Distributors';
    IF v_cnt = 0 THEN
        INSERT INTO SUPPLIER (supplier_name, contact_person, phone, email, address)
        VALUES ('MedPlus Distributors', 'Mr. Rajesh Sharma', '+91 98401 23456', 'rajesh@medplusdist.com', 'Plot 45, Guindy Industrial Estate, Chennai');
    END IF;

    SELECT COUNT(*) INTO v_cnt FROM SUPPLIER WHERE supplier_name = 'Apollo Healthcare Logistics';
    IF v_cnt = 0 THEN
        INSERT INTO SUPPLIER (supplier_name, contact_person, phone, email, address)
        VALUES ('Apollo Healthcare Logistics', 'Ms. Sunita Reddy', '+91 98402 34567', 'sunita.reddy@apollologistics.in', '12 Greams Road, Thousand Lights, Chennai');
    END IF;

    SELECT COUNT(*) INTO v_cnt FROM SUPPLIER WHERE supplier_name = 'Cipla Regional Supply Depot';
    IF v_cnt = 0 THEN
        INSERT INTO SUPPLIER (supplier_name, contact_person, phone, email, address)
        VALUES ('Cipla Regional Supply Depot', 'Mr. Amitav Sen', '+91 98403 45678', 'chennai.depot@ciplasupply.com', 'Sector 3, Ambattur Industrial Estate, Chennai');
    END IF;

    SELECT COUNT(*) INTO v_cnt FROM SUPPLIER WHERE supplier_name = 'Sun Pharma Distributorship';
    IF v_cnt = 0 THEN
        INSERT INTO SUPPLIER (supplier_name, contact_person, phone, email, address)
        VALUES ('Sun Pharma Distributorship', 'Mr. Vignesh Natarajan', '+91 98404 56789', 'vignesh.n@sunpharmaagency.com', '78 OMR Road, Kandanchavadi, Chennai');
    END IF;

    SELECT COUNT(*) INTO v_cnt FROM SUPPLIER WHERE supplier_name = 'Glenmark Life Sciences Supply';
    IF v_cnt = 0 THEN
        INSERT INTO SUPPLIER (supplier_name, contact_person, phone, email, address)
        VALUES ('Glenmark Life Sciences Supply', 'Dr. Meera Nambiar', '+91 98405 67890', 'm.nambiar@glenmarksupply.org', '15 GST Road, Tambaram, Chennai');
    END IF;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('>> Suppliers seeded successfully.');
END;
/

-- ----------------------------------------------------------------------------
-- 2. SEED MEDICINES
-- ----------------------------------------------------------------------------
DECLARE
    v_cnt NUMBER;
    v_sup1 NUMBER;
    v_sup2 NUMBER;
    v_sup3 NUMBER;
    v_sup4 NUMBER;
    v_sup5 NUMBER;
BEGIN
    SELECT supplier_id INTO v_sup1 FROM SUPPLIER WHERE supplier_name = 'MedPlus Distributors';
    SELECT supplier_id INTO v_sup2 FROM SUPPLIER WHERE supplier_name = 'Apollo Healthcare Logistics';
    SELECT supplier_id INTO v_sup3 FROM SUPPLIER WHERE supplier_name = 'Cipla Regional Supply Depot';
    SELECT supplier_id INTO v_sup4 FROM SUPPLIER WHERE supplier_name = 'Sun Pharma Distributorship';
    SELECT supplier_id INTO v_sup5 FROM SUPPLIER WHERE supplier_name = 'Glenmark Life Sciences Supply';

    -- 1. Paracetamol 650mg
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Paracetamol 650mg' AND batch_number = 'PCM-2025-01';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Paracetamol 650mg', 'Antipyretic', 'Fast-acting fever and mild to moderate pain relief', 2.50, 180, 30, 'PCM-2025-01', ADD_MONTHS(TRUNC(SYSDATE), 18), v_sup1);
    END IF;

    -- 2. Amoxicillin 500mg
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Amoxicillin 500mg' AND batch_number = 'AMX-2025-04';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Amoxicillin 500mg', 'Antibiotic', 'Broad-spectrum penicillin antibiotic for bacterial infections', 12.00, 75, 20, 'AMX-2025-04', ADD_MONTHS(TRUNC(SYSDATE), 12), v_sup3);
    END IF;

    -- 3. Azithromycin 500mg
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Azithromycin 500mg' AND batch_number = 'AZI-2024-09';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Azithromycin 500mg', 'Antibiotic', 'Macrolide antibiotic for respiratory and skin infections', 24.50, 45, 15, 'AZI-2024-09', ADD_MONTHS(TRUNC(SYSDATE), 10), v_sup3);
    END IF;

    -- 4. Metformin 500mg (Low Stock Demo)
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Metformin 500mg' AND batch_number = 'MET-2024-11';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Metformin 500mg', 'Antidiabetic', 'First-line medication for type 2 diabetes glycemic control', 4.50, 8, 20, 'MET-2024-11', ADD_MONTHS(TRUNC(SYSDATE), 14), v_sup4);
    END IF;

    -- 5. Amlodipine 5mg
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Amlodipine 5mg' AND batch_number = 'AML-2025-02';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Amlodipine 5mg', 'Antihypertensive', 'Calcium channel blocker for hypertension management', 3.75, 120, 25, 'AML-2025-02', ADD_MONTHS(TRUNC(SYSDATE), 22), v_sup4);
    END IF;

    -- 6. Pantoprazole 40mg
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Pantoprazole 40mg' AND batch_number = 'PAN-2025-03';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Pantoprazole 40mg', 'Gastrointestinal', 'Proton pump inhibitor reducing stomach acid reflux', 8.25, 95, 20, 'PAN-2025-03', ADD_MONTHS(TRUNC(SYSDATE), 16), v_sup2);
    END IF;

    -- 7. Cetirizine 10mg (Near Expiry Demo - Expiring within 25 days)
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Cetirizine 10mg' AND batch_number = 'CET-2024-02';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Cetirizine 10mg', 'Antihistamine', 'Second-generation antihistamine for seasonal allergy relief', 3.00, 35, 15, 'CET-2024-02', TRUNC(SYSDATE) + 20, v_sup1);
    END IF;

    -- 8. Ibuprofen 400mg (Expired Demo - Expired 15 days ago)
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Ibuprofen 400mg' AND batch_number = 'IBU-2023-08';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Ibuprofen 400mg', 'Analgesic', 'Nonsteroidal anti-inflammatory drug (NSAID) for inflammation', 5.00, 15, 10, 'IBU-2023-08', TRUNC(SYSDATE) - 15, v_sup2);
    END IF;

    -- 9. Vitamin C 500mg Chewable
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Vitamin C 500mg' AND batch_number = 'VTC-2025-07';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Vitamin C 500mg', 'Vitamin', 'Immune support dietary supplement and antioxidant', 2.00, 250, 40, 'VTC-2025-07', ADD_MONTHS(TRUNC(SYSDATE), 24), v_sup5);
    END IF;

    -- 10. Oseltamivir 75mg (Critical Low Stock Demo - 2 units)
    SELECT COUNT(*) INTO v_cnt FROM MEDICINE WHERE medicine_name = 'Oseltamivir 75mg' AND batch_number = 'OST-2024-10';
    IF v_cnt = 0 THEN
        INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
        VALUES ('Oseltamivir 75mg', 'Antiviral', 'Antiviral agent indicated for acute influenza treatment', 65.00, 2, 10, 'OST-2024-10', ADD_MONTHS(TRUNC(SYSDATE), 8), v_sup5);
    END IF;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('>> Medicines seeded successfully.');
END;
/

-- ----------------------------------------------------------------------------
-- 3. SEED PATIENTS
-- ----------------------------------------------------------------------------
DECLARE
    v_cnt NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_cnt FROM PATIENT WHERE phone = '+91 94441 11222';
    IF v_cnt = 0 THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Karthik Ramanathan', 42, 'Male', '+91 94441 11222', '45 Gandhi Road, Velachery, Chennai');
    END IF;

    SELECT COUNT(*) INTO v_cnt FROM PATIENT WHERE phone = '+91 94442 22333';
    IF v_cnt = 0 THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Priya Venkatesh', 29, 'Female', '+91 94442 22333', '18 Nehru Street, Adyar, Chennai');
    END IF;

    SELECT COUNT(*) INTO v_cnt FROM PATIENT WHERE phone = '+91 94443 33444';
    IF v_cnt = 0 THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Dr. Ananya Sundaram', 63, 'Female', '+91 94443 33444', '8 Temple View Apartments, Mylapore, Chennai');
    END IF;

    SELECT COUNT(*) INTO v_cnt FROM PATIENT WHERE phone = '+91 94444 44555';
    IF v_cnt = 0 THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Balaji Sridhar', 51, 'Male', '+91 94444 44555', '92 Anna Nagar West, Chennai');
    END IF;

    SELECT COUNT(*) INTO v_cnt FROM PATIENT WHERE phone = '+91 94445 55666';
    IF v_cnt = 0 THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Deepa Ranganathan', 35, 'Female', '+91 94445 55666', '33 Harrington Road, Chetpet, Chennai');
    END IF;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('>> Patients seeded successfully.');
END;
/

-- ----------------------------------------------------------------------------
-- 4. SEED PRESCRIPTIONS & PRESCRIPTION_ITEMS
-- ----------------------------------------------------------------------------
DECLARE
    v_cnt NUMBER;
    v_pat1 NUMBER;
    v_pat2 NUMBER;
    v_pat3 NUMBER;
    v_pres1 NUMBER;
    v_pres2 NUMBER;
    v_med_para NUMBER;
    v_med_amox NUMBER;
    v_med_amlo NUMBER;
    v_med_metf NUMBER;
BEGIN
    SELECT patient_id INTO v_pat1 FROM PATIENT WHERE phone = '+91 94441 11222';
    SELECT patient_id INTO v_pat2 FROM PATIENT WHERE phone = '+91 94442 22333';
    SELECT patient_id INTO v_pat3 FROM PATIENT WHERE phone = '+91 94443 33444';

    SELECT medicine_id INTO v_med_para FROM MEDICINE WHERE medicine_name = 'Paracetamol 650mg' AND ROWNUM = 1;
    SELECT medicine_id INTO v_med_amox FROM MEDICINE WHERE medicine_name = 'Amoxicillin 500mg' AND ROWNUM = 1;
    SELECT medicine_id INTO v_med_amlo FROM MEDICINE WHERE medicine_name = 'Amlodipine 5mg' AND ROWNUM = 1;
    SELECT medicine_id INTO v_med_metf FROM MEDICINE WHERE medicine_name = 'Metformin 500mg' AND ROWNUM = 1;

    -- Prescription 1 for Karthik
    SELECT COUNT(*) INTO v_cnt FROM PRESCRIPTION WHERE patient_id = v_pat1 AND doctor_name = 'Dr. K. Swaminathan';
    IF v_cnt = 0 THEN
        INSERT INTO PRESCRIPTION (patient_id, doctor_name, diagnosis, prescription_date, notes)
        VALUES (v_pat1, 'Dr. K. Swaminathan', 'Acute Upper Respiratory Tract Infection', TRUNC(SYSDATE) - 2, 'Take complete course of antibiotics.')
        RETURNING prescription_id INTO v_pres1;

        INSERT INTO PRESCRIPTION_ITEMS (prescription_id, medicine_id, dosage, quantity)
        VALUES (v_pres1, v_med_amox, '1 capsule three times daily for 5 days', 15);

        INSERT INTO PRESCRIPTION_ITEMS (prescription_id, medicine_id, dosage, quantity)
        VALUES (v_pres1, v_med_para, '1 tablet SOS for body pain or fever', 10);
    END IF;

    -- Prescription 2 for Ananya (Hypertension & Diabetes)
    SELECT COUNT(*) INTO v_cnt FROM PRESCRIPTION WHERE patient_id = v_pat3 AND doctor_name = 'Dr. Radhika Menon';
    IF v_cnt = 0 THEN
        INSERT INTO PRESCRIPTION (patient_id, doctor_name, diagnosis, prescription_date, notes)
        VALUES (v_pat3, 'Dr. Radhika Menon', 'Essential Hypertension & Type 2 Diabetes Mellitus', TRUNC(SYSDATE) - 5, 'Monthly routine refill. Check HbA1c in 3 months.')
        RETURNING prescription_id INTO v_pres2;

        INSERT INTO PRESCRIPTION_ITEMS (prescription_id, medicine_id, dosage, quantity)
        VALUES (v_pres2, v_med_amlo, '1 tablet once daily in the morning', 30);

        INSERT INTO PRESCRIPTION_ITEMS (prescription_id, medicine_id, dosage, quantity)
        VALUES (v_pres2, v_med_metf, '1 tablet twice daily with breakfast and dinner', 60);
    END IF;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('>> Prescriptions and Items seeded successfully.');
END;
/

-- ----------------------------------------------------------------------------
-- 5. SEED BILLS & BILL_ITEMS
-- ----------------------------------------------------------------------------
DECLARE
    v_cnt NUMBER;
    v_pat1 NUMBER;
    v_pat2 NUMBER;
    v_bill1 NUMBER;
    v_bill2 NUMBER;
    v_med_para NUMBER;
    v_med_panto NUMBER;
    v_med_vitc NUMBER;
BEGIN
    SELECT patient_id INTO v_pat1 FROM PATIENT WHERE phone = '+91 94441 11222';
    SELECT patient_id INTO v_pat2 FROM PATIENT WHERE phone = '+91 94442 22333';

    SELECT medicine_id INTO v_med_para FROM MEDICINE WHERE medicine_name = 'Paracetamol 650mg' AND ROWNUM = 1;
    SELECT medicine_id INTO v_med_panto FROM MEDICINE WHERE medicine_name = 'Pantoprazole 40mg' AND ROWNUM = 1;
    SELECT medicine_id INTO v_med_vitc FROM MEDICINE WHERE medicine_name = 'Vitamin C 500mg' AND ROWNUM = 1;

    -- Bill 1: Registered Patient Bill
    SELECT COUNT(*) INTO v_cnt FROM BILL WHERE bill_number = 'INV-2026-0001';
    IF v_cnt = 0 THEN
        -- subtotal: 10 * 2.50 + 10 * 8.25 = 25.00 + 82.50 = 107.50
        -- tax: 5%, total = 107.50 * 1.05 = 112.88
        INSERT INTO BILL (bill_number, patient_id, customer_name, bill_date, subtotal, discount_pct, tax_pct, total_amount, payment_method)
        VALUES ('INV-2026-0001', v_pat1, 'Karthik Ramanathan', CURRENT_TIMESTAMP - INTERVAL '1' DAY, 107.50, 0.00, 5.00, 112.88, 'UPI')
        RETURNING bill_id INTO v_bill1;

        INSERT INTO BILL_ITEMS (bill_id, medicine_id, medicine_name, unit_price, quantity, line_total)
        VALUES (v_bill1, v_med_para, 'Paracetamol 650mg', 2.50, 10, 25.00);

        INSERT INTO BILL_ITEMS (bill_id, medicine_id, medicine_name, unit_price, quantity, line_total)
        VALUES (v_bill1, v_med_panto, 'Pantoprazole 40mg', 8.25, 10, 82.50);
    END IF;

    -- Bill 2: Walk-In Counter Purchase (Today)
    SELECT COUNT(*) INTO v_cnt FROM BILL WHERE bill_number = 'INV-2026-0002';
    IF v_cnt = 0 THEN
        -- subtotal: 20 * 2.00 = 40.00
        -- discount: 10%, total = 36.00
        INSERT INTO BILL (bill_number, patient_id, customer_name, bill_date, subtotal, discount_pct, tax_pct, total_amount, payment_method)
        VALUES ('INV-2026-0002', NULL, 'Walk-in Customer (Mr. S. Kumar)', CURRENT_TIMESTAMP, 40.00, 10.00, 0.00, 36.00, 'CASH')
        RETURNING bill_id INTO v_bill2;

        INSERT INTO BILL_ITEMS (bill_id, medicine_id, medicine_name, unit_price, quantity, line_total)
        VALUES (v_bill2, v_med_vitc, 'Vitamin C 500mg', 2.00, 20, 40.00);
    END IF;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('>> Bills and Items seeded successfully.');
END;
/

PROMPT ============================================================================
PROMPT Sample seed data populated successfully and verified.
PROMPT ============================================================================
EXIT;
