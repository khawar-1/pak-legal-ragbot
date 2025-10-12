#!/usr/bin/env python3
"""
Test script to demonstrate the intent classification and requirement extraction system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intent_classifier import IntentClassifier
from requirement_extractor import CloudRequirementExtractor
import json

def test_intent_classification():
    """Test the intent classification system"""
    print("=" * 60)
    print("TESTING INTENT CLASSIFICATION")
    print("=" * 60)
    
    classifier = IntentClassifier()
    
    test_inputs = [
        "How does AWS Lambda work?",
        "I'm building an e-commerce platform that needs to handle 10,000 users",
        "Hello, how are you today?",
        "What's the best way to store user data in AWS?",
        "We have a mobile app with real-time messaging features",
        "Can you explain AWS VPC networking?",
        "Our startup is creating a social media platform for 1M users",
        "What's the weather like?"
    ]
    
    for user_input in test_inputs:
        print(f"\nInput: '{user_input}'")
        try:
            result = classifier.classify_intent(user_input)
            print(f"Intent: {result['intent']}")
            print(f"Confidence: {result['confidence']:.2f}")
            print(f"Reasoning: {result['reasoning']}")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 40)

def test_requirement_extraction():
    """Test the requirement extraction system"""
    print("\n" + "=" * 60)
    print("TESTING REQUIREMENT EXTRACTION")
    print("=" * 60)
    
    extractor = CloudRequirementExtractor()
    
    test_projects = [
        "I'm building a web application for a small business that needs to handle about 500 users, store customer data and files, and integrate with payment systems.",
        "We're developing a mobile app for food delivery that needs real-time GPS tracking, push notifications, and should handle 50,000 concurrent users during peak hours.",
        "Our startup is creating a social media platform similar to Twitter that needs to handle millions of users, store media files, and provide real-time messaging capabilities."
    ]
    
    for i, project_description in enumerate(test_projects, 1):
        print(f"\nProject {i}: {project_description}")
        print("-" * 40)
        try:
            requirements = extractor.extract_requirements(project_description)
            print(f"Application Type: {requirements['application_type']}")
            print(f"User Scale: {requirements['user_scale']['traffic_volume']}")
            print(f"Data Types: {requirements['data_requirements']['data_types']}")
            print(f"Real-time Features: {requirements['real_time_features']}")
            print(f"AWS Recommendations: {requirements['aws_recommendations']}")
            print(f"Confidence Score: {requirements['confidence_score']:.2f}")
            
            # Generate summary
            summary = extractor.generate_recommendation_summary(requirements)
            print(f"\nRecommendation Summary:\n{summary}")
            
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 60)

def main():
    """Run all tests"""
    print("AWS Cloud Assistant - Intent Classification & Requirement Extraction Test")
    print("Make sure Ollama is running with the required models!")
    
    try:
        test_intent_classification()
        test_requirement_extraction()
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED!")
        print("=" * 60)
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure Ollama is running and the required models are available.")

if __name__ == "__main__":
    main()
