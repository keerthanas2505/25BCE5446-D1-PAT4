-- ============================================================================
-- HOSPITAL PHARMACY MANAGEMENT SYSTEM (HPMS)
-- Database: PostgreSQL 15+ / Neon / Supabase
-- Seed Data Script (seed_data_postgres.sql)
-- Safe, Idempotent Demonstration Data
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SEED SUPPLIERS
-- ----------------------------------------------------------------------------
INSERT INTO SUPPLIER (supplier_name, contact_person, phone, email, address)
VALUES 
    ('MedPlus Distributors', 'Mr. Rajesh Sharma', '+91 98401 23456', 'rajesh@medplusdist.com', 'Plot 45, Guindy Industrial Estate, Chennai'),
    ('Apollo Healthcare Logistics', 'Ms. Sunita Reddy', '+91 98402 34567', 'sunita.reddy@apollologistics.in', '12 Greams Road, Thousand Lights, Chennai'),
    ('Cipla Regional Supply Depot', 'Mr. Amitav Sen', '+91 98403 45678', 'chennai.depot@ciplasupply.com', 'Sector 3, Ambattur Industrial Estate, Chennai'),
    ('Sun Pharma Distributorship', 'Mr. Vignesh Natarajan', '+91 98404 56789', 'vignesh.n@sunpharmaagency.com', '78 OMR Road, Kandanchavadi, Chennai'),
    ('Glenmark Life Sciences Supply', 'Dr. Meera Nambiar', '+91 98405 67890', 'm.nambiar@glenmarksupply.org', '15 GST Road, Tambaram, Chennai')
ON CONFLICT (supplier_name) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 2. SEED MEDICINES
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_sup1 INTEGER;
    v_sup2 INTEGER;
    v_sup3 INTEGER;
    v_sup4 INTEGER;
    v_sup5 INTEGER;
BEGIN
    SELECT supplier_id INTO v_sup1 FROM SUPPLIER WHERE supplier_name = 'MedPlus Distributors';
    SELECT supplier_id INTO v_sup2 FROM SUPPLIER WHERE supplier_name = 'Apollo Healthcare Logistics';
    SELECT supplier_id INTO v_sup3 FROM SUPPLIER WHERE supplier_name = 'Cipla Regional Supply Depot';
    SELECT supplier_id INTO v_sup4 FROM SUPPLIER WHERE supplier_name = 'Sun Pharma Distributorship';
    SELECT supplier_id INTO v_sup5 FROM SUPPLIER WHERE supplier_name = 'Glenmark Life Sciences Supply';

    INSERT INTO MEDICINE (medicine_name, category, description, unit_price, quantity, reorder_threshold, batch_number, expiry_date, supplier_id)
    VALUES 
        ('Paracetamol 650mg', 'Antipyretic', 'Fast-acting fever and mild to moderate pain relief', 2.50, 180, 30, 'PCM-2025-01', CURRENT_DATE + INTERVAL '18 months', v_sup1),
        ('Amoxicillin 500mg', 'Antibiotic', 'Broad-spectrum penicillin antibiotic for bacterial infections', 12.00, 75, 20, 'AMX-2025-04', CURRENT_DATE + INTERVAL '12 months', v_sup3),
        ('Azithromycin 500mg', 'Antibiotic', 'Macrolide antibiotic for respiratory and skin infections', 24.50, 45, 15, 'AZI-2024-09', CURRENT_DATE + INTERVAL '10 months', v_sup3),
        ('Metformin 500mg', 'Antidiabetic', 'First-line medication for type 2 diabetes glycemic control', 4.50, 8, 20, 'MET-2024-11', CURRENT_DATE + INTERVAL '14 months', v_sup4),
        ('Amlodipine 5mg', 'Antihypertensive', 'Calcium channel blocker for hypertension management', 3.75, 120, 25, 'AML-2025-02', CURRENT_DATE + INTERVAL '22 months', v_sup4),
        ('Pantoprazole 40mg', 'Gastrointestinal', 'Proton pump inhibitor reducing stomach acid reflux', 8.25, 95, 20, 'PAN-2025-03', CURRENT_DATE + INTERVAL '16 months', v_sup2),
        ('Cetirizine 10mg', 'Antihistamine', 'Second-generation antihistamine for seasonal allergy relief', 3.00, 35, 15, 'CET-2024-02', CURRENT_DATE + INTERVAL '20 days', v_sup1),
        ('Ibuprofen 400mg', 'Analgesic', 'Nonsteroidal anti-inflammatory drug (NSAID) for inflammation', 5.00, 15, 10, 'IBU-2023-08', CURRENT_DATE - INTERVAL '15 days', v_sup2),
        ('Vitamin C 500mg', 'Vitamin', 'Immune support dietary supplement and antioxidant', 2.00, 250, 40, 'VTC-2025-07', CURRENT_DATE + INTERVAL '24 months', v_sup5),
        ('Oseltamivir 75mg', 'Antiviral', 'Antiviral agent indicated for acute influenza treatment', 65.00, 2, 10, 'OST-2024-10', CURRENT_DATE + INTERVAL '8 months', v_sup5)
    ON CONFLICT (medicine_name, batch_number) DO NOTHING;
END $$;

-- ----------------------------------------------------------------------------
-- 3. SEED PATIENTS
-- ----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM PATIENT WHERE phone = '+91 94441 11222') THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Karthik Ramanathan', 42, 'Male', '+91 94441 11222', '45 Gandhi Road, Velachery, Chennai');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM PATIENT WHERE phone = '+91 94442 22333') THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Priya Venkatesh', 29, 'Female', '+91 94442 22333', '18 Nehru Street, Adyar, Chennai');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM PATIENT WHERE phone = '+91 94443 33444') THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Dr. Ananya Sundaram', 63, 'Female', '+91 94443 33444', '8 Temple View Apartments, Mylapore, Chennai');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM PATIENT WHERE phone = '+91 94444 44555') THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Balaji Sridhar', 51, 'Male', '+91 94444 44555', '92 Anna Nagar West, Chennai');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM PATIENT WHERE phone = '+91 94445 55666') THEN
        INSERT INTO PATIENT (name, age, gender, phone, address)
        VALUES ('Deepa Ranganathan', 35, 'Female', '+91 94445 55666', '33 Harrington Road, Chetpet, Chennai');
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 4. SEED PRESCRIPTIONS & PRESCRIPTION_ITEMS
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_pat1 INTEGER;
    v_pat3 INTEGER;
    v_pres1 INTEGER;
    v_pres2 INTEGER;
    v_med_para INTEGER;
    v_med_amox INTEGER;
    v_med_amlo INTEGER;
    v_med_metf INTEGER;
BEGIN
    SELECT patient_id INTO v_pat1 FROM PATIENT WHERE phone = '+91 94441 11222' LIMIT 1;
    SELECT patient_id INTO v_pat3 FROM PATIENT WHERE phone = '+91 94443 33444' LIMIT 1;

    SELECT medicine_id INTO v_med_para FROM MEDICINE WHERE medicine_name = 'Paracetamol 650mg' LIMIT 1;
    SELECT medicine_id INTO v_med_amox FROM MEDICINE WHERE medicine_name = 'Amoxicillin 500mg' LIMIT 1;
    SELECT medicine_id INTO v_med_amlo FROM MEDICINE WHERE medicine_name = 'Amlodipine 5mg' LIMIT 1;
    SELECT medicine_id INTO v_med_metf FROM MEDICINE WHERE medicine_name = 'Metformin 500mg' LIMIT 1;

    IF v_pat1 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM PRESCRIPTION WHERE patient_id = v_pat1 AND doctor_name = 'Dr. K. Swaminathan') THEN
        INSERT INTO PRESCRIPTION (patient_id, doctor_name, diagnosis, prescription_date, notes)
        VALUES (v_pat1, 'Dr. K. Swaminathan', 'Acute Upper Respiratory Tract Infection', CURRENT_DATE - INTERVAL '2 days', 'Take complete course of antibiotics.')
        RETURNING prescription_id INTO v_pres1;

        INSERT INTO PRESCRIPTION_ITEMS (prescription_id, medicine_id, dosage, quantity)
        VALUES 
            (v_pres1, v_med_amox, '1 capsule three times daily for 5 days', 15),
            (v_pres1, v_med_para, '1 tablet SOS for body pain or fever', 10);
    END IF;

    IF v_pat3 IS NOT NULL AND NOT EXISTS (SELECT 1 FROM PRESCRIPTION WHERE patient_id = v_pat3 AND doctor_name = 'Dr. Radhika Menon') THEN
        INSERT INTO PRESCRIPTION (patient_id, doctor_name, diagnosis, prescription_date, notes)
        VALUES (v_pat3, 'Dr. Radhika Menon', 'Essential Hypertension & Type 2 Diabetes Mellitus', CURRENT_DATE - INTERVAL '5 days', 'Monthly routine refill. Check HbA1c in 3 months.')
        RETURNING prescription_id INTO v_pres2;

        INSERT INTO PRESCRIPTION_ITEMS (prescription_id, medicine_id, dosage, quantity)
        VALUES 
            (v_pres2, v_med_amlo, '1 tablet once daily in the morning', 30),
            (v_pres2, v_med_metf, '1 tablet twice daily with breakfast and dinner', 60);
    END IF;
END $$;

-- ----------------------------------------------------------------------------
-- 5. SEED BILLS & BILL_ITEMS
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    v_pat1 INTEGER;
    v_bill1 INTEGER;
    v_bill2 INTEGER;
    v_med_para INTEGER;
    v_med_panto INTEGER;
    v_med_vitc INTEGER;
BEGIN
    SELECT patient_id INTO v_pat1 FROM PATIENT WHERE phone = '+91 94441 11222' LIMIT 1;

    SELECT medicine_id INTO v_med_para FROM MEDICINE WHERE medicine_name = 'Paracetamol 650mg' LIMIT 1;
    SELECT medicine_id INTO v_med_panto FROM MEDICINE WHERE medicine_name = 'Pantoprazole 40mg' LIMIT 1;
    SELECT medicine_id INTO v_med_vitc FROM MEDICINE WHERE medicine_name = 'Vitamin C 500mg' LIMIT 1;

    IF NOT EXISTS (SELECT 1 FROM BILL WHERE bill_number = 'INV-2026-0001') THEN
        INSERT INTO BILL (bill_number, patient_id, customer_name, bill_date, subtotal, discount_pct, tax_pct, total_amount, payment_method)
        VALUES ('INV-2026-0001', v_pat1, 'Karthik Ramanathan', CURRENT_TIMESTAMP - INTERVAL '1 day', 107.50, 0.00, 5.00, 112.88, 'UPI')
        RETURNING bill_id INTO v_bill1;

        INSERT INTO BILL_ITEMS (bill_id, medicine_id, medicine_name, unit_price, quantity, line_total)
        VALUES 
            (v_bill1, v_med_para, 'Paracetamol 650mg', 2.50, 10, 25.00),
            (v_bill1, v_med_panto, 'Pantoprazole 40mg', 8.25, 10, 82.50);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM BILL WHERE bill_number = 'INV-2026-0002') THEN
        INSERT INTO BILL (bill_number, patient_id, customer_name, bill_date, subtotal, discount_pct, tax_pct, total_amount, payment_method)
        VALUES ('INV-2026-0002', NULL, 'Walk-in Customer (Mr. S. Kumar)', CURRENT_TIMESTAMP, 40.00, 10.00, 0.00, 36.00, 'CASH')
        RETURNING bill_id INTO v_bill2;

        INSERT INTO BILL_ITEMS (bill_id, medicine_id, medicine_name, unit_price, quantity, line_total)
        VALUES (v_bill2, v_med_vitc, 'Vitamin C 500mg', 2.00, 20, 40.00);
    END IF;
END $$;
