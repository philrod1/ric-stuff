#!/bin/bash
#kubectl get pods --all-namespaces --field-selector=status.phase=Failed | grep Evicted | awk '{print "kubectl delete pod " $2 " -n " $1}' | bash
kubectl get pods --all-namespaces --field-selector=status.phase=Failed | awk '{print "kubectl delete pod " $2 " -n " $1}' | bash
kubectl get pods --all-namespaces --field-selector=status.phase=Succeeded | grep Completed | awk '{print "kubectl delete pod " $2 " -n " $1}' | bash