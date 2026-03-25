#!/bin/bash

gcloud compute start-iap-tunnel microstrategy-one 3306 --local-host-port=localhost:27002 --zone=us-east1-b