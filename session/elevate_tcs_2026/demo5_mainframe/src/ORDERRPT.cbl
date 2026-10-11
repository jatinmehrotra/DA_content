       IDENTIFICATION DIVISION.
       PROGRAM-ID. ORDERRPT.
      *----------------------------------------------------------------
      * Reads order records, totals the amounts, and flags any order
      * over the large-order threshold. Business logic deliberately
      * simple so AWS Transform can extract and document it clearly.
      *----------------------------------------------------------------
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ORDER-FILE ASSIGN TO ORDIN
               ORGANIZATION IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  ORDER-FILE.
       COPY ORDREC.

       WORKING-STORAGE SECTION.
       01  WS-EOF                 PIC X(01) VALUE 'N'.
       01  WS-TOTAL               PIC 9(09)V99 VALUE 0.
       01  WS-COUNT               PIC 9(05) VALUE 0.
       01  WS-LARGE-THRESHOLD     PIC 9(07)V99 VALUE 2000.00.
       01  WS-LARGE-COUNT         PIC 9(05) VALUE 0.

       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT ORDER-FILE
           PERFORM UNTIL WS-EOF = 'Y'
               READ ORDER-FILE
                   AT END
                       MOVE 'Y' TO WS-EOF
                   NOT AT END
                       PERFORM PROCESS-ORDER
               END-READ
           END-PERFORM
           CLOSE ORDER-FILE
           PERFORM PRINT-SUMMARY
           STOP RUN.

       PROCESS-ORDER.
           ADD ORD-AMOUNT TO WS-TOTAL
           ADD 1 TO WS-COUNT
           IF ORD-AMOUNT > WS-LARGE-THRESHOLD
               ADD 1 TO WS-LARGE-COUNT
               DISPLAY 'LARGE ORDER: ' ORD-ID ' = ' ORD-AMOUNT
           END-IF.

       PRINT-SUMMARY.
           DISPLAY '------------------------------'
           DISPLAY 'ORDERS PROCESSED: ' WS-COUNT
           DISPLAY 'TOTAL AMOUNT:     ' WS-TOTAL
           DISPLAY 'LARGE ORDERS:     ' WS-LARGE-COUNT.
