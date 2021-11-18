#!/usr/bin/python
#coding: utf-8

import config

model = 'pins'

def test_pins(client, api_standard_tests):
    assert api_standard_tests(
        client = client, 
        model = model
    )
