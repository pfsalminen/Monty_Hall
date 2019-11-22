import json

data = {
    "BuilderMT" : {
        "ITEM_Category" : '''SELECT
    Cost_Code AS RecordSource_FKey,
    Cost_Code AS cat_CategoryID,
    CC_Description AS cat_Desc,
    0 AS SITE_ID
FROM JCCOSTCODE''',
        "VENDOR" : '''SELECT 
    SUB_AP_NUMBER AS RecordSource_FKey, 
    SUB_AP_NUMBER AS ven_VendorID, 
    SUB_NAME AS ven_VendorName, 
    SUB_ADDRESS AS ven_Address1, 
    SUB_ADDRESS_2 AS ven_Address2, 
    SUB_CITY AS ven_City, 
    SUB_STATE AS ven_StateCD, 
    SUB_POSTCODE AS ven_Zip, 
    PHONE AS Vendor_Phone, 
    FAX AS Vendor_Fax, 
    SUB_CONTACT_WRTY_EMAIL as ven_Email, 
    0 AS SITE_ID 
FROM SUPPLIER 
WHERE SUB_AP_NUMBER IS NOT NULL  
AND SUB_AP_NUMBER <> "" 
AND SUB_NAME <> "" ''',
        "PROJECT" : '''SELECT DISTINCT
    SALES_AREA AS RecordSource_FKey,
    SALES_AREA AS proj_Code,
    AREA_DESC AS proj_Desc,
    AREA_CITY AS proj_city,
    AREA_POSTCODE as proj_Zip,
    AREA_STATE AS proj_stateCD,
    1 AS SITE_ID
FROM AREA
WHERE SALES_AREA <> "" 
AND SALES_AREA IS NOT NULL 
AND SALES_AREA <> " " ''', 
        "JOB" : '''SELECT 
    JOB.JOB_NUMBER AS RecordSource_FKey, 
    AREA.SALES_AREA AS proj_Code, 
    ACNT_JOB_NUMBER AS job_JobID, 
    SITEADDRESS1 AS job_address1, 
    SITEADDRESS2 AS job_address2, 
    SITECITY AS job_City, 
    SITESTATE AS job_StateCD, 
    SITEPCODE AS job_Zip, 
    LOT_NUMBER || "/" || LOT_BLOCK_CODE  as job_LotBlock, 
    1 AS SITE_ID, 
    SCHEDULE.ACTUAL_START_DATE AS job_WarrantyDate_Start, 
    SCHEDULE.ACTUAL_END_DATE AS job_WarrantyDate_Closed 
FROM JOB 
    INNER JOIN AREA ON JOB.AREA_ID = AREA.AREA_ID 
    LEFT OUTER JOIN SCHEDULE ON JOB.JOB_NUMBER = SCHEDULE.JOB_NUMBER 
WHERE SALES_AREA <> "" AND SALES_AREA IS NOT NULL AND SALES_AREA <> " " ''',
        "JOB_Contact" : '''SELECT
    ("P" || JOB_NUMBER) AS RecordSource_FKey,
    OWNERNAME AS cont_FullName,
    ACNT_JOB_NUMBER AS job_JobID,
    OWNERADDRESS1 AS cont_Address1,
    OWNEREMAIL AS CONT_EMAIL,
    OWNERPHONE1 AS JOB_CONTACT_PHONE1,
    "1" AS JOB_CONTACT_PHONE1_TYPE,
    OWNERPHONE2 AS JOB_CONTACT_PHONE2,
    "7" AS JOB_CONTACT_PHONE2_TYPE,
    OWNERMOBILE AS JOB_CONTACT_PHONE3,
    "2" AS JOB_CONTACT_PHONE3_TYPE,
    OWNERFAX AS JOB_CONTACT_PHONE4,
    "4" AS JOB_CONTACT_PHONE4_TYPE,
    OWNERSUBURB AS cont_City,
    OWNERSTATE AS Cont_StateCD,
    OWNERPOSTCODE   AS Cont_Zip,
    1 AS PrimaryContact,
    1 AS SITE_ID
FROM JOB
WHERE OWNERNAME IS NOT NULL AND OWNERNAME <> "" ''', 
        "JOB_Plans" : '''SELECT 
    JOB_NUMBER AS RecordSource_FKey,
    ACNT_JOB_NUMBER AS job_JobID,
    HOUSE_MODEL_NAME AS Title,
    1 AS SITE_ID
FROM JOB
INNER JOIN AREA ON JOB.AREA_ID = AREA.AREA_ID
WHERE HOUSE_MODEL_NAME IS NOT NULL 
AND SALES_AREA <> "" 
AND SALES_AREA IS NOT NULL 
AND SALES_AREA <> " " ''',
        "VENDOR_EMP" : '''SELECT
    (SUB_AP_NUMBER || "-" || SUB_CONTACT) AS RecordSource_FKey,
    SUB_AP_NUMBER AS ven_VendorID,
    SUB_CONTACT AS cont_FullName,
    SUB_ADDRESS AS cont_Address1,
    SUB_ADDRESS_2 AS cont_Address2,
    SUB_CITY AS cont_City,
    SUB_STATE AS cont_StateCD,
    SUB_POSTCODE AS cont_Zip,
    PHONE AS VENDOR_CONTACT_PHONE1,
    FAX AS VENDOR_CONTACT_PHONE2,
    "MAIN" AS VENDOR_CONTACT_PHONE1_TYPE,
    "FAX" AS VENDOR_CONTACT_PHONE2_TYPE,
    SUB_CONTACT_EMAIL as cont_Email,
    1 As cont_PrimaryContact,
    0 As cont_SecondaryContact,
    0 AS SITE_ID
FROM SUPPLIER
WHERE SUB_AP_NUMBER IS NOT NULL 
AND SUB_CONTACT IS NOT NULL 
AND SUB_CONTACT <> "" ''', 
        "VENDOR_EMP_2" : '''SELECT
    (SUB_AP_NUMBER || "-" || SUB_CONTACT_2) AS RecordSource_FKey,
    SUB_AP_NUMBER AS ven_VendorID,
    SUB_CONTACT_2 AS cont_FullName,
    SUB_ADDRESS AS cont_Address1,
    SUB_ADDRESS_2 AS cont_Address2,
    SUB_CITY AS cont_City,
    SUB_STATE AS cont_StateCD,
    SUB_POSTCODE AS cont_Zip,
    PHONE AS VENDOR_CONTACT_PHONE1,
    FAX AS VENDOR_CONTACT_PHONE2,
    "MAIN" AS VENDOR_CONTACT_PHONE1_TYPE,
    "FAX" AS VENDOR_CONTACT_PHONE2_TYPE,
    SUB_CONTACT_2_EMAIL as cont_Email,
    1 As cont_PrimaryContact,
    0 As cont_SecondaryContact,
    0 AS SITE_ID
FROM SUPPLIER
WHERE SUB_AP_NUMBER IS NOT NULL 
AND SUB_CONTACT_2 IS NOT NULL 
AND SUB_CONTACT_2 <> "" ''',
        "VENDOR_EMP_3" : '''SELECT 
    (SUB_AP_NUMBER || "-" || SUB_CONTACT_WRTY) AS RecordSource_FKey,
    SUB_AP_NUMBER AS ven_VendorID,
    SUB_CONTACT_WRTY AS cont_FullName,
    SUB_ADDRESS AS CONT_Address1,
    SUB_ADDRESS_2 AS CONT_Address2,
    SUB_CITY AS CONT_City,
    SUB_STATE AS CONT_StateCD,
    SUB_POSTCODE AS CONT_Zip,
    SUB_PHONE_WRTY AS VENDOR_CONTACT_PHONE1,
    SUB_FAX_WRTY AS VENDOR_CONTACT_PHONE2,
    SUB_CONTACT_WRTY_MOBILE as VENDOR_CONTACT_PHONE3,
    "MAIN" AS VENDOR_CONTACT_PHONE1_TYPE,
    "FAX" AS VENDOR_CONTACT_PHONE2_TYPE,
    "CELL" AS VENDOR_CONTACT_PHONE3_TYPE,
    SUB_CONTACT_WRTY_EMAIL as cont_email,
    1 As Cont_PrimaryContact,
    0 As Cont_SecondaryContact,
    0 AS SITE_ID
FROM SUPPLIER
WHERE SUB_AP_NUMBER IS NOT NULL 
AND SUB_CONTACT_WRTY IS NOT NULL 
AND SUB_CONTACT_WRTY <> "" ''', 
        "DEFAULT_VENDORS" : '''SELECT DISTINCT
    JOB.ACNT_JOB_NUMBER AS JOB_JOBID,
    POVENDOR AS VEN_VENDORID,
    POCOSTCODE AS COSTCODE,
    1 AS SITE_ID
FROM POHEADER
INNER JOIN JOB ON POHEADER.POJOBNUMBER = JOB.JOB_NUMBER
INNER JOIN PODETAIL ON POHEADER.POHEADER_ID = PODETAIL.POHEADER_ID''',
    },
    "Timberline" : {
        "VENDOR" : '''SELECT
    Vendor AS RecordSource_FKey,
    Vendor AS ven_VendorID,
    Name AS ven_VendorName,
    Address_1 AS ven_Address1,
    Address_2 AS ven_Address2,
    City AS ven_City,
    State AS ven_StateCD,
    ZIP AS ven_Zip,
    Telephone AS VENDOR_Phone,
    Fax_Number AS VENDOR_Fax,
    Contact_1_Email_Address as Ven_Email,
    Auto_Ins_Company AS ven_INS_AutoCompany,
    Auto_Ins_Policy_Num AS ven_INS_AutoCert,
    Auto_Ins_Effect_Dt AS Auto_Effective,
    Auto_Ins_Expir_Dt AS ven_INS_AutoDate,
    GL_Ins_Company AS ven_INS_LiabilityCompany,
    GL_Ins_Policy_Number AS ven_INS_LiabilityCert,
    GL_Ins_Effective_Dt AS GL_Effective,
    GL_Ins_Expiration_Dt AS ven_INS_LiabilityDate,
    Work_Comp_Ins_Cmpany AS ven_INS_WorkmansCompCompany,
    Work_Comp_Policy_Num AS ven_INS_WorkmansCompCert,
    Work_Comp_Effect_Dt AS Work_Effective,
    Work_Comp_Expir_Dt AS ven_INS_WorkmansCompDate,
    Umbrella_Ins_Company AS ven_INS_UmbrellaCompany,
    Umb_Ins_Policy_Num AS ven_INS_UmbrellaCert,
    Umb_Ins_Effective_Dt AS Umbrella_Effective,
    Umb_Ins_Expir_Dt AS ven_INS_UmbrellaDate,
    Customer_Number AS CustomerNumber,
    0 AS SITE_ID
FROM MASTER_APM_VENDOR''',
        "ITEM_Category" : '''SELECT
    Cost_Code AS RecordSource_FKey,
    Cost_Code AS cat_CategoryID,
    Description AS cat_Desc,
    0 AS SITE_ID
FROM MASTER_JCM_STANDARD_COST_CODE''',
        "PROJECT" : '''SELECT DISTINCT
    Left(MASTER_JCM_JOB_1.Job,(InStr(1,MASTER_JCM_JOB_1.Job,"-")-1)) AS RecordSource_FKey,
    Left(MASTER_JCM_JOB_1.Job,(InStr(1,MASTER_JCM_JOB_1.Job,"-")-1)) AS proj_Code,
    "Imported From Timberline" AS proj_Desc,
    AREA_CITY AS proj_CITY,
    AREA_STATE AS proj_STATECD,
    AREA_POSTCODE AS proj_ZIP,
    1 AS SITE_ID
FROM MASTER_JCM_JOB_1''',
        "JOB" : '''SELECT
    MASTER_JCM_JOB_1.Job AS RecordSource_FKey,
    MID(MASTER_JCM_JOB_1.Job,(InStr(1,MASTER_JCM_JOB_1.Job,"-") + 1), 2) AS proj_Code,
    MASTER_JCM_JOB_1.Job AS job_JobID,
    MASTER_JCM_JOB_1.Address_1 AS job_address1,
    MASTER_JCM_JOB_1.Address_2 AS job_address2,
    MASTER_JCM_JOB_1.City AS job_City,
    MASTER_JCM_JOB_1.State AS job_StateCD,
    MASTER_JCM_JOB_1.ZIP_Code AS job_Zip,
    RIGHT(MASTER_JCM_JOB_1.JOB,3) AS job_LotBlock,
    MASTER_JCM_JOB_1.Actual_Complete_Date AS job_WarrantyDate_Closed, 	MASTER_JCM_JOB_1.Actual_Start_Date AS job_WarrantyDate_Start,
    MASTER_JCM_JOB_1.contract_Date AS Job_WarrantyDate_contracted,
    1 AS SITE_ID
FROM MASTER_JCM_JOB_1''',
        "JOB_Contact" : '''SELECT
    ("P" & MASTER_JCM_JOB_1.Job) AS RecordSource_FKey,
    MASTER_JCM_JOB_1.CUSTOMER_NAME AS cont_FullName,
    MASTER_JCM_JOB_1.Job AS job_JobID,
    Customer_City AS Cont_City,
    Customer_State AS Cont_StateCD,
    Customer_ZIP_Code  AS Cont_Zip,
    MASTER_JCM_JOB_1.Address_1 AS cont_Address1,
    MASTER_JCM_JOB_1.Address_2 AS cont_Address2,
    MASTER_JCM_JOB_1.CUSTOMER_CONTACT_1 AS CONT_EMAIL,
    MASTER_JCM_JOB_1.CUSTOMER_PHONE_1 AS JOB_CONTACT_PHONE1,
    "1" AS JOB_CONTACT_PHONE1_TYPE,
    MASTER_JCM_JOB_1.CUSTOMER_PHONE_2 AS JOB_CONTACT_PHONE2,
    "7" AS JOB_CONTACT_PHONE2_TYPE,
    MASTER_JCM_JOB_1.CUSTOMER_FAX AS JOB_CONTACT_PHONE3,
    "4" AS JOB_CONTACT_PHONE3_TYPE,
    1 AS PrimaryContact,
    1 AS SITE_ID
FROM MASTER_JCM_JOB_1
WHERE CUSTOMER_NAME IS NOT NULL AND CUSTOMER_NAME <> "" ''', 
        "JOB_Plans" : '''SELECT
    Job AS RecordSource_Fkey,
    Job AS job_JobID,
    House_Type AS Title,
    1 AS SITE_ID
FROM MASTER_JCM_JOB_1
WHERE Job IS NOT NULL AND Job 
AND House_Type IS NOT NULL 
AND House_Type <> "" ''', 
        "VENDOR_ToJob" : '''SELECT DISTINCT
            job AS job_JobID,
            Cost_Code AS cat_CategoryID,
            Vendor AS ven_VendorID,
            1 AS SITE_ID
        FROM MASTER_APM_DISTRIBUTION
        WHERE Job IS NOT NULL 
        AND Job <> "" 
        AND Amount not like "%-%" '''
    }
}

with open('scripts.json', 'w') as f:
    json.dump(data, f)