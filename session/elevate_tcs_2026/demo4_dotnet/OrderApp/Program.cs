using System;
using System.Collections.Generic;
using System.Configuration;

namespace OrderApp
{
    // .NET Framework 4.7.2 console app. Uses ConfigurationManager (full-framework
    // style) and classic C# idioms so the AWS Transform .NET agent has something
    // concrete to modernize when porting to cross-platform .NET 8+.
    class Program
    {
        static void Main(string[] args)
        {
            string region = ConfigurationManager.AppSettings["Region"] ?? "us-east-1";
            Console.WriteLine("Order App starting in region: " + region);

            List<string> orders = new List<string>();
            orders.Add("A-1001:Acme:1299.00");
            orders.Add("A-1002:Globex:499.50");
            orders.Add("A-1003:Initech:2750.75");

            double total = 0.0;
            foreach (string entry in orders)
            {
                string[] parts = entry.Split(':');
                double amount = double.Parse(parts[2]);
                total += amount;
                Console.WriteLine("Order " + parts[0] + " for " + parts[1] + " = $" + amount);
            }

            Console.WriteLine("Total = $" + total);
        }
    }
}
