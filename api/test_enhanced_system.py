#!/usr/bin/env python3
"""
Test script for the enhanced intent-based chatbot system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_intent_classifier import BinaryIntentClassifier
from requirement_extraction_system import CloudRequirementExtractor
from conversation_context import ConversationManager
import json

def test_intent_classification():
    """Test the binary intent classification system"""
    print("=" * 60)
    print("TESTING BINARY INTENT CLASSIFICATION")
    print("=" * 60)
    
    classifier = BinaryIntentClassifier()
    
    test_inputs = [
        # AWS Query Examples
        "How does AWS Lambda work?",
        "What's the best way to store data in AWS?",
        "Explain S3 bucket policies",
        "Compare Lambda vs EC2",
        "How to set up a VPC?",
        
        # Project Requirements Examples
        "I'm building an e-commerce platform",
        "We need to handle 10,000 concurrent users",
        "Creating a social media app for startups",
        "Building a mobile app with real-time features",
        "Our company needs a data analytics platform"
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
    print("TESTING REQUIREMENT EXTRACTION SYSTEM")
    print("=" * 60)
    
    extractor = CloudRequirementExtractor()
    
    test_projects = [
        "Building an e-commerce platform for 5000 users with product catalog and payment processing",
        "Creating a social media app",
        "We need a mobile application that handles real-time messaging for 50k users"
    ]
    
    for i, project_description in enumerate(test_projects, 1):
        print(f"\nProject {i}: {project_description}")
        print("-" * 40)
        try:
            result = extractor.extract_requirements(project_description)
            print(f"Response Type: {result['type']}")
            print(f"Status: {result['status']}")
            
            if result['type'] == 'requirement_follow_up':
                print(f"Progress: {result['progress']}")
                print(f"Missing Fields: {result['missing_fields']}")
                print(f"Follow-up Questions: {len(result['follow_up_questions'])}")
            elif result['type'] == 'complete_requirements':
                print(f"Requirements extracted: {len(result['requirements'])} categories")
            
            print(f"Message: {result['message']}")
            
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 60)

def main():
    """Run all tests"""
    print("Enhanced Intent-Based Chatbot System Test")
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
