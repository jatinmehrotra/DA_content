      *----------------------------------------------------------------
      * ORDREC - Order record layout (copybook)
      *----------------------------------------------------------------
       01  ORDER-RECORD.
           05  ORD-ID              PIC X(06).
           05  ORD-CUSTOMER        PIC X(20).
           05  ORD-AMOUNT          PIC 9(07)V99.
           05  ORD-STATUS          PIC X(01).
               88  ORD-OPEN        VALUE 'O'.
               88  ORD-CLOSED      VALUE 'C'.
