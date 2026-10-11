//ORDERRPT JOB (ACCT),'ORDER REPORT',CLASS=A,MSGCLASS=X
//*-------------------------------------------------------------------
//* Runs the ORDERRPT COBOL program against the order master file.
//*-------------------------------------------------------------------
//STEP01   EXEC PGM=ORDERRPT
//STEPLIB  DD DSN=PROD.LOADLIB,DISP=SHR
//ORDIN    DD DSN=PROD.ORDER.MASTER,DISP=SHR
//SYSOUT   DD SYSOUT=*
//SYSPRINT DD SYSOUT=*
