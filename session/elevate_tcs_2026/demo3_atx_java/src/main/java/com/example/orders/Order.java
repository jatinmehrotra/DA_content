package com.example.orders;

import java.util.Date;

/*
 * Old-style Java 8 model class. Deliberately uses pre-modern idioms so the
 * AWS Transform upgrade (Java 8 -> 17/21) produces a readable, demo-friendly diff:
 *   - java.util.Date instead of java.time
 *   - verbose getters, no records
 */
public class Order {
    private String id;
    private String customer;
    private double amount;
    private Date createdOn;

    public Order(String id, String customer, double amount, Date createdOn) {
        this.id = id;
        this.customer = customer;
        this.amount = amount;
        this.createdOn = createdOn;
    }

    public String getId() { return id; }
    public String getCustomer() { return customer; }
    public double getAmount() { return amount; }
    public Date getCreatedOn() { return createdOn; }
}
