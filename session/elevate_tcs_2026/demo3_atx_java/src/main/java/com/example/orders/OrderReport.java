package com.example.orders;

import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.List;

/*
 * Deliberately pre-modern Java 8 style:
 *   - no 'var'
 *   - explicit Iterator loop instead of streams
 *   - String concatenation instead of String.format / text blocks
 * The AWS Transform agent should modernize these when upgrading the language level.
 */
public class OrderReport {

    public static void main(String[] args) {
        List<Order> orders = new ArrayList<Order>();
        orders.add(new Order("A-1001", "Acme Corp", 1299.00, new Date()));
        orders.add(new Order("A-1002", "Globex", 499.50, new Date()));
        orders.add(new Order("A-1003", "Initech", 2750.75, new Date()));

        double total = 0.0;
        for (Iterator<Order> it = orders.iterator(); it.hasNext();) {
            Order o = it.next();
            total = total + o.getAmount();
            String line = "Order " + o.getId() + " for " + o.getCustomer()
                    + " = $" + o.getAmount();
            System.out.println(line);
        }

        System.out.println("------------------------------");
        System.out.println("Total across " + orders.size() + " orders = $" + total);
    }
}
