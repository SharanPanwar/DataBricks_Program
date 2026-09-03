# Databricks notebook source
landing_path = "abfss://practice-ecommerce@stpracticeecom.dfs.core.windows.net/landing/customers/"

display(dbutils.fs.ls(landing_path))