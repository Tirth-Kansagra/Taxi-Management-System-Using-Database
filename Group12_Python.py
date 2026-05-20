import psycopg2  # For PostgreSQL (use pymysql for MySQL)
from psycopg2 import sql

# Establish database connection
connection = psycopg2.connect(
    host="localhost",
    database="Taxi Management System",
    user="postgres",
    password="12345678"
)

cursor = connection.cursor()

# List of queries to execute
queries = [
    # 1
    """
    SELECT d.DriverId, d.Name, d.PhoneNo
    FROM TaxiManagement.Driver AS d
    WHERE d.AvlStatus = TRUE;
    """,
    
    # 2
    """
    SELECT d.DriverId, d.Name, COUNT(rb.RideID) / COUNT(DISTINCT DATE(rb.RideDate)) AS AvgRidesPerDay
    FROM TaxiManagement.RideBooking AS rb
    JOIN TaxiManagement.Driver AS d ON rb.DriverID = d.DriverId
    WHERE rb.Status = 'completed'
    GROUP BY d.DriverId, d.Name;
    """,

    # 3
    """
    SELECT d.DriverId, d.Name, SUM(r.Fare) AS TotalFare,
           DENSE_RANK() OVER ( ORDER BY SUM(r.Fare) DESC ) AS Rank
    FROM TaxiManagement.RideBooking r
    JOIN TaxiManagement.Driver d ON r.DriverID = d.DriverId
    WHERE r.Status = 'completed'
    GROUP BY d.DriverId, d.Name;
    """,
    
    # 4
    """
    SELECT a.AdID, a.Name, COUNT(t.PlateNumber) AS TaxiCount
    FROM TaxiManagement.DriverTaxiCoordinator AS a
    JOIN TaxiManagement.Taxi AS t ON a.AdID = t.AdID
    GROUP BY a.AdID, a.Name
    HAVING COUNT(t.PlateNumber) > (
        SELECT AVG(TaxiCount)
        FROM (
            SELECT COUNT(t2.PlateNumber) AS TaxiCount
            FROM TaxiManagement.Taxi t2
            GROUP BY t2.AdID
        ) AS AvgTaxisPerAdmin
    );
    """,

    # 5
    """
    SELECT d.DriverId, d.Name, d.PhoneNo, d.Email, AVG(f.Rating) AS AvgRating
    FROM TaxiManagement.Driver d
    JOIN TaxiManagement.RideBooking rb ON d.DriverId = rb.DriverID
    JOIN TaxiManagement.Feedback f ON rb.CustomerID = f.CustomerID
    GROUP BY d.DriverId, d.Name, d.PhoneNo, d.Email
    HAVING AVG(f.Rating) > 4;
    """,

    # 6
    """
    SELECT d.DriverId, d.Name
    FROM TaxiManagement.Driver d
    WHERE NOT EXISTS (
        SELECT rb.CustomerID
        FROM TaxiManagement.RideBooking rb
        WHERE rb.DriverID = d.DriverId
        AND NOT EXISTS (
            SELECT f.FeedbackID
            FROM TaxiManagement.Feedback f
            WHERE f.CustomerID = rb.CustomerID
        )
    );
    """,

    # 7
    """
    SELECT D.DriverID, D.Name, S.Hours
    FROM TaxiManagement.Driver D
    JOIN TaxiManagement.Shift S ON D.DriverID = S.DriverID
    WHERE S.Hours > (SELECT AVG(Hours) FROM TaxiManagement.Shift);
    """,

    # 8 (Empty Query)
    """
    SELECT C . AdID , C . Name , AVG ( TotalEarnings ) AS AvgDriverEarnings
    FROM TaxiManagement . DriverTaxiCoordinator AS C
    JOIN TaxiManagement . Gets AS G ON C . AdID = G . AdID
    JOIN (
    SELECT D . DriverID , SUM ( P . Fare ) AS TotalEarnings
    FROM TaxiManagement . Driver AS D
    JOIN TaxiManagement . RideBooking R ON D . DriverID = R . DriverID
    JOIN TaxiManagement . Payment P ON R . RideID = P . RideID
    WHERE R . Status = 'completed'
    GROUP BY D . DriverID
    ) AS DriverEarnings ON G . DriverID = DriverEarnings . DriverID
    GROUP BY C . AdID , C . Name
    ORDER BY AvgDriverEarnings DESC ;
    """,

    # 9
    """
    SELECT C.CustomerID, C.Name, COUNT(R.RideID) AS TotalRides, SUM(P.Fare) AS TotalFare
    FROM TaxiManagement.Customer C
    JOIN TaxiManagement.RideBooking R ON C.CustomerID = R.CustomerID
    JOIN TaxiManagement.Payment P ON R.RideID = P.RideID
    WHERE R.Status = 'completed'
    GROUP BY C.CustomerID, C.Name
    HAVING COUNT(R.RideID) >= 2 AND SUM(P.Fare) > 400;
    """,

    # 10
    """
    SELECT D.DriverID, D.Name, COUNT(R.RideID) AS TotalRides
    FROM TaxiManagement.Driver D
    JOIN TaxiManagement.RideBooking R ON D.DriverID = R.DriverID
    WHERE D.AvlStatus = TRUE AND R.Status = 'completed'
    GROUP BY D.DriverID, D.Name
    HAVING COUNT(R.RideID) >= 3;
    """,

    # 11
    """
    SELECT C.CustomerID, C.Name, SUM(P.Fare) AS TotalFare
    FROM TaxiManagement.Customer C
    JOIN TaxiManagement.RideBooking R ON C.CustomerID = R.CustomerID
    JOIN TaxiManagement.Payment P ON R.RideID = P.RideID
    GROUP BY C.CustomerID, C.Name
    HAVING SUM(P.Fare) > (
        SELECT AVG(TotalFare)
        FROM (
            SELECT SUM(P.Fare) AS TotalFare
            FROM TaxiManagement.Customer C
            JOIN TaxiManagement.RideBooking R ON C.CustomerID = R.CustomerID
            JOIN TaxiManagement.Payment P ON R.RideID = P.RideID
            GROUP BY C.CustomerID
        ) AS AllCustomerFares
    );
    """,

    # 12
    """
    SELECT d.DriverId, d.Name, d.PhoneNo, d.Email, d.AvlStatus
    FROM TaxiManagement.Driver d
    LEFT JOIN TaxiManagement.RideBooking r ON d.DriverId = r.DriverID AND r.RideDate = '2024-10-01'
    WHERE r.RideID IS NULL;
    """,

    # 13
    """
    SELECT RB.CurrentLocation, RB.Destination, COUNT(RB.RideID) AS BookingCount,
           DENSE_RANK() OVER (ORDER BY COUNT(RB.RideID) DESC) AS Rank
    FROM TaxiManagement.RideBooking RB
    GROUP BY RB.CurrentLocation, RB.Destination
    ORDER BY BookingCount DESC
    LIMIT 3;
    """,

    # 14
    """
    SELECT C.CustomerID, C.Name, COUNT(RB.RideID) AS TotalRides
    FROM TaxiManagement.Customer C
    JOIN TaxiManagement.RideBooking RB ON C.CustomerID = RB.CustomerID
    GROUP BY C.CustomerID, C.Name
    ORDER BY TotalRides DESC
    LIMIT 5;
    """,

    # 15
    """
    SELECT D.DriverId, D.Name, AVG(EXTRACT(EPOCH FROM (S.Shiftend - S.Shiftstart))) / 3600 AS AvgShiftHours
    FROM TaxiManagement.Driver D
    JOIN TaxiManagement.Shift S ON D.DriverId = S.DriverId
    GROUP BY D.DriverId, D.Name
    ORDER BY AvgShiftHours DESC;
    """,

    # 16
    """
    SELECT C.CustomerID, C.Name, COUNT(RB.RideID) AS TotalRides,
           CASE 
               WHEN COUNT(RB.RideID) > 10 THEN 'Frequent'
               WHEN COUNT(RB.RideID) BETWEEN 5 AND 10 THEN 'Occasional'
               ELSE 'Rare'
           END AS BookingFrequency
    FROM TaxiManagement.Customer C
    LEFT JOIN TaxiManagement.RideBooking RB ON C.CustomerID = RB.CustomerID
    GROUP BY C.CustomerID, C.Name
    ORDER BY TotalRides DESC;
    """,

    # 17
    """
    SELECT D.DriverId, D.Name
    FROM TaxiManagement.Driver D
    LEFT JOIN TaxiManagement.RideBooking R ON D.DriverId = R.DriverID
    LEFT JOIN TaxiManagement.Feedback F ON R.CustomerID = F.CustomerID
    WHERE F.FeedbackID IS NULL
      OR R.RideDate < CURRENT_DATE - INTERVAL '1 month'
    GROUP BY D.DriverId, D.Name;
    """,

    # 18
    """
    SELECT D.DriverId, D.Name, EXTRACT(HOUR FROM S.Shiftstart) AS ShiftStartHour,
           SUM(RB.Fare) AS TotalRevenue
    FROM TaxiManagement.Driver AS D
    JOIN TaxiManagement.RideBooking AS RB ON D.DriverId = RB.DriverID
    JOIN TaxiManagement.Shift AS S ON D.DriverId = S.DriverId
    GROUP BY D.DriverId, D.Name, EXTRACT(HOUR FROM S.Shiftstart)
    ORDER BY TotalRevenue DESC;
    """,

    # 19
    """
    SELECT RB.Destination, COUNT(RB.RideID) AS RideCount
    FROM TaxiManagement.RideBooking RB
    WHERE RB.RideDate >= CURRENT_DATE - INTERVAL '1 MONTH'
    GROUP BY RB.Destination
    ORDER BY RideCount DESC
    LIMIT 10;
    """,

    # 20
    """
    SELECT C.CustomerID, C.Name
    FROM TaxiManagement.Customer C
    JOIN TaxiManagement.RideBooking RB ON C.CustomerID = RB.CustomerID
    WHERE RB.DriverID = 101
    GROUP BY C.CustomerID, C.Name
    HAVING COUNT(DISTINCT RB.DriverID) = 1;
    """,

    # 21
    """
    WITH OverallAverageFare AS (
        SELECT AVG(Fare) AS AvgFare
        FROM TaxiManagement.RideBooking
    ),
    RouteFareCounts AS (
        SELECT RB.CurrentLocation, RB.Destination, COUNT(RB.RideID) AS BookingCount,
               AVG(RB.Fare) AS AverageFare
        FROM TaxiManagement.RideBooking RB
        GROUP BY RB.CurrentLocation, RB.Destination
    )
    SELECT RFC.CurrentLocation, RFC.Destination, RFC.BookingCount, RFC.AverageFare,
           OAF.AvgFare
    FROM RouteFareCounts RFC, OverallAverageFare OAF
    WHERE RFC.AverageFare > OAF.AvgFare
    ORDER BY RFC.BookingCount DESC;
    """
]

# Execute all queries
for i, query in enumerate(queries, start=1):
    cursor.execute(query)
    if query.strip().lower().startswith("select"):
        result = cursor.fetchall()
        print(f"Result of Query {i}: {result}")
    else:
        print(f"Query {i} executed successfully.")

# Close cursor and connection
cursor.close()
connection.close()
