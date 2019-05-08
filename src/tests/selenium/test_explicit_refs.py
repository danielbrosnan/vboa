"""
Automated tests for the explicit_refs tab

Written by DEIMOS Space S.L. (femd)

module vboa
"""
import os
import sys
import unittest
import time
import subprocess
import datetime
import tests.selenium.functions as functions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import ActionChains,TouchActions
from selenium.webdriver.common.keys import Keys

# Import engine of the DDBB
import eboa.engine.engine as eboa_engine
from eboa.engine.engine import Engine
from eboa.engine.query import Query
from eboa.datamodel.base import Session, engine, Base
from eboa.engine.errors import UndefinedEventLink, DuplicatedEventLinkRef, WrongPeriod, SourceAlreadyIngested, WrongValue, OddNumberOfCoordinates, EboaResourcesPathNotAvailable, WrongGeometry

# Import datamodel
from eboa.datamodel.dim_signatures import DimSignature
from eboa.datamodel.alerts import Alert
from eboa.datamodel.events import Event, EventLink, EventKey, EventText, EventDouble, EventObject, EventGeometry, EventBoolean, EventTimestamp
from eboa.datamodel.gauges import Gauge
from eboa.datamodel.sources import Source, SourceStatus
from eboa.datamodel.explicit_refs import ExplicitRef, ExplicitRefGrp, ExplicitRefLink
from eboa.datamodel.annotations import Annotation, AnnotationCnf, AnnotationText, AnnotationDouble, AnnotationObject, AnnotationGeometry, AnnotationBoolean, AnnotationTimestamp


class TestEngine(unittest.TestCase):
    def setUp(self):
        # Create the engine to manage the data
        self.engine_eboa = Engine()
        self.query_eboa = Query()

        # Create session to connect to the database
        self.session = Session()

        # Clear all tables before executing the test
        self.query_eboa.clear_db()

        self.options = Options()
        self.options.headless = True
        subprocess.call(["pkill", "firefox"])

    def tearDown(self):
        # Close connections to the DDBB
        self.engine_eboa.close_session()
        self.query_eboa.close_session()
        self.session.close()

    def test_explicit_refs_query_no_filter(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "events": [{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT",
                "gauge": {"name": "GAUGE_NAME",
                          "system": "GAUGE_SYSTEM",
                          "insertion_type": "SIMPLE_UPDATE"},
                "start": "2018-06-05T04:07:03",
                "stop": "2018-06-05T06:07:36"
                },{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT_2",
                "gauge": {"name": "GAUGE_NAME_2",
                          "system": "GAUGE_SYSTEM_2",
                          "insertion_type": "SIMPLE_UPDATE"},
                "start": "2018-06-05T04:07:12",
                "stop": "2018-06-05T06:07:24"
                }]
            }]}

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))

        driver.quit()

        assert number_of_elements == 2

    # Input "In" not working
    def test_explicit_refs_query_explicit_ref_filter(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_1.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "events": [{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT_1",
                "gauge": {"name": "GAUGE_NAME",
                          "system": "GAUGE_SYSTEM",
                          "insertion_type": "SIMPLE_UPDATE"},
                "start": "2018-06-05T04:07:03",
                "stop": "2018-06-05T06:07:36"
                },{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT_2",
                "gauge": {"name": "GAUGE_NAME_2",
                          "system": "GAUGE_SYSTEM_2",
                          "insertion_type": "SIMPLE_UPDATE"},
                "start": "2018-06-05T04:07:12",
                "stop": "2018-06-05T06:07:24"
                }]
            },{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_2.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "events": [{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT_3",
                "gauge": {"name": "GAUGE_NAME_3",
                          "system": "GAUGE_SYSTEM_3",
                          "insertion_type": "SIMPLE_UPDATE"},
                "start": "2018-06-05T04:07:05",
                "stop": "2018-06-05T06:07:31"
                }]
            }
        ]}

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## Like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the explicit_ref_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[1]/div[1]/input")
        inputElement.send_keys("EXPLICIT_REFERENCE_EVENT_2")

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 1 and empty_element is False

        ## Not like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the explicit_ref_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[1]/div[1]/input")
        inputElement.send_keys("EXPLICIT_REFERENCE_EVENT_2")

        notLikeButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[1]/div[1]/label")
        if not notLikeButton.find_element_by_xpath("input").is_selected():
            notLikeButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 2

        ## In ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the explicit_ref_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[1]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("EXPLICIT_REFERENCE_EVENT_1")
        inputElement.send_keys(Keys.RETURN)
        inputElement.click()
        inputElement.send_keys("EXPLICIT_REFERENCE_EVENT_3")
        inputElement.send_keys(Keys.RETURN)

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0d")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 2

        ## Not in ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the explicit_ref_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[1]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("EXPLICIT_REFERENCE_EVENT_2")
        inputElement.send_keys(Keys.RETURN)

        notInButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[1]/div[2]/label")
        if not notInButton.find_element_by_xpath("input").is_selected():
            notInButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generate
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 2

    def test_explicit_refs_query_group_filter(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_1.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "explicit_references": [{
                "group": "EXPL_GROUP_1",
                "name": "EXPLICIT_REFERENCE_1",
                "links": [{"name": "LINK_NAME_1",
                       "link": "EXPLICIT_REFERENCE_LINK_1"}]
                },{
                "group": "EXPL_GROUP_2",
                "name": "EXPLICIT_REFERENCE_2",
                "links": [{"name": "LINK_NAME_2",
                       "link": "EXPLICIT_REFERENCE_LINK_2"}]
                }]
            },{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_2.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "explicit_references": [{
                "group": "EXPL_GROUP_1",
                "name": "EXPLICIT_REFERENCE_3",
                "links": [{"name": "LINK_NAME_3",
                       "link": "EXPLICIT_REFERENCE_LINK_3"}]
                }]
            }
        ]}

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## Like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the group_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[2]/div[1]/input")
        inputElement.send_keys("EXPL_GROUP_2")

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 1 and empty_element is False

        ## Not like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the group_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[2]/div[1]/input")
        inputElement.send_keys("EXPL_GROUP_2")

        notLikeButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[2]/div[1]/label")
        if not notLikeButton.find_element_by_xpath("input").is_selected():
            notLikeButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 2

        ## In ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the group_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[2]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("EXPL_GROUP_1")
        inputElement.send_keys(Keys.RETURN)

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 2

        ## Not in ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the group_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[2]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("EXPL_GROUP_2")
        inputElement.send_keys(Keys.RETURN)

        notInButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[2]/div[2]/label")
        if not notInButton.find_element_by_xpath("input").is_selected():
            notInButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generate
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 2

    #Source filter not working
    def test_explicit_refs_query_source_filter(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_1.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "explicit_references": [{
                "group": "EXPL_GROUP_1",
                "name": "EXPLICIT_REFERENCE_1"
                },{
                "group": "EXPL_GROUP_2",
                "name": "EXPLICIT_REFERENCE_2"
                }]
            },{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_2.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "explicit_references": [{
                "group": "EXPL_GROUP_1",
                "name": "EXPLICIT_REFERENCE_3"
                }]
            }
        ]}

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## Like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the source_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[3]/div[1]/input")
        inputElement.send_keys("source_1.xml")

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 1 and empty_element is False

        ## Not like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the source_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[3]/div[1]/input")
        inputElement.send_keys("source_2.xml")

        notLikeButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[3]/div[1]/label")
        if not notLikeButton.find_element_by_xpath("input").is_selected():
            notLikeButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 2

        ## In ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the source_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[3]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("source_2.xml")
        inputElement.send_keys(Keys.RETURN)

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))

        assert number_of_elements == 2

        ## Not in ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the source_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[3]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("source_2.xml")
        inputElement.send_keys(Keys.RETURN)

        notInButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[3]/div[2]/label")
        if not notInButton.find_element_by_xpath("input").is_selected():
            notInButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generate
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 2

    def test_explicit_refs_query_gauge_name_filter(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_1.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "events": [{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT_1",
                "gauge": {"name": "GAUGE_NAME_1",
                          "system": "GAUGE_SYSTEM_1",
                          "insertion_type": "EVENT_KEYS"},
                "start": "2018-06-05T04:07:03",
                "stop": "2018-06-05T06:07:36",
                "key": "EVENT_KEY"
                },{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT_2",
                "gauge": {"name": "GAUGE_NAME_2",
                          "system": "GAUGE_SYSTEM_2",
                          "insertion_type": "EVENT_KEYS"},
                "start": "2018-06-05T04:07:12",
                "stop": "2018-06-05T06:07:24",
                "key": "EVENT_KEY_2"
                }]
            },{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_2.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "events": [{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT_2",
                "gauge": {"name": "GAUGE_NAME_2",
                          "system": "GAUGE_SYSTEM_2",
                          "insertion_type": "EVENT_KEYS"},
                "start": "2018-06-05T04:07:05",
                "stop": "2018-06-05T06:07:31",
                "key": "EVENT_KEY_3"
                }]
            }
        ]}

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## Like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the gauge_name_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[1]/div[2]/div[1]/div[1]/input")
        inputElement.send_keys("GAUGE_NAME_1")

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 1 and empty_element is False

        ## Not like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the gauge_name_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[1]/div[2]/div[1]/div[1]/input")
        inputElement.send_keys("GAUGE_NAME_1")

        notLikeButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[1]/div[2]/div[1]/div[1]/label")
        if not notLikeButton.find_element_by_xpath("input").is_selected():
            notLikeButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 2

        ## In ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the gauge_name_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[1]/div[2]/div[2]/div[1]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("GAUGE_NAME_2")
        inputElement.send_keys(Keys.RETURN)

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 2

        ## Not in ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the gauge_name_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[1]/div[2]/div[2]/div[1]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("GAUGE_NAME_1")
        inputElement.send_keys(Keys.RETURN)

        notInButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[1]/div[2]/div[2]/div[1]/label")
        if not notInButton.find_element_by_xpath("input").is_selected():
            notInButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generate
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 2

    def test_explicit_refs_query_gauge_system_filter(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_1.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "events": [{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT",
                "gauge": {"name": "GAUGE_NAME_1",
                          "system": "GAUGE_SYSTEM_1",
                          "insertion_type": "EVENT_KEYS"},
                "start": "2018-06-05T04:07:03",
                "stop": "2018-06-05T06:07:36",
                "key": "EVENT_KEY"
                },{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT_2",
                "gauge": {"name": "GAUGE_NAME_2",
                          "system": "GAUGE_SYSTEM_2",
                          "insertion_type": "EVENT_KEYS"},
                "start": "2018-06-05T04:07:12",
                "stop": "2018-06-05T06:07:24",
                "key": "EVENT_KEY_2"
                }]
            },{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_2.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "events": [{
                "explicit_reference": "EXPLICIT_REFERENCE_EVENT",
                "gauge": {"name": "GAUGE_NAME_2",
                          "system": "GAUGE_SYSTEM_2",
                          "insertion_type": "EVENT_KEYS"},
                "start": "2018-06-05T04:07:05",
                "stop": "2018-06-05T06:07:31",
                "key": "EVENT_KEY_3"
                }]
            }
        ]}

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## Like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the gauge_system_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[1]/div/div/div/div/div/form/div[4]/div[1]/div[2]/input")
        inputElement.send_keys("GAUGE_SYSTEM_1")

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 1 and empty_element is False

        ## Not like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the gauge_system_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[1]/div/div/div/div/div/form/div[4]/div[1]/div[2]/input")
        inputElement.send_keys("GAUGE_SYSTEM_1")

        notLikeButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[1]/div/div/div/div/div/form/div[4]/div[1]/div[2]/label")
        if not notLikeButton.find_element_by_xpath("input").is_selected():
            notLikeButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 2

        ## In ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the gauge_system_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[1]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("GAUGE_SYSTEM_2")
        inputElement.send_keys(Keys.RETURN)

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 2

        ## Not in ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the gauge_system_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[1]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("GAUGE_SYSTEM_1")
        inputElement.send_keys(Keys.RETURN)

        notInButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[1]/div/div/div/div/div/form/div[4]/div[2]/div[2]/label")
        if not notInButton.find_element_by_xpath("input").is_selected():
            notInButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generate
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 2

    def test_explicit_refs_query_annotation_name_filter(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE_1",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_1.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "annotations": [{
                "explicit_reference" : "EXPLICIT_REFERENCE_1",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": []
                    }]
                }]
            },{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE_2",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_2.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "annotations": [{
                "explicit_reference" : "EXPLICIT_REFERENCE_2",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": []
                    }]
                },{
                "explicit_reference" : "EXPLICIT_REFERENCE_2",
                "annotation_cnf": {
                    "name": "NAME_2",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": []
                    }]
                }]
            }]
        }

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## Like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the annotation_name_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[1]/div[1]/input")
        inputElement.send_keys("NAME_2")

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 1 and empty_element is False

        ## Not like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the annotation_name_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[1]/div[2]/div[1]/div[1]/input")
        inputElement.send_keys("NAME_2")

        notLikeButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[1]/div[1]/label")
        if not notLikeButton.find_element_by_xpath("input").is_selected():
            notLikeButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 2

        ## In ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the annotation_name_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[2]/div[1]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("NAME_1")
        inputElement.send_keys(Keys.RETURN)

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 2

        ## Not in ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the annotation_name_in input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[2]/div[1]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("NAME_2")
        inputElement.send_keys(Keys.RETURN)

        notInButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[2]/div[1]/label")
        if not notInButton.find_element_by_xpath("input").is_selected():
            notInButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generate
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 2

    def test_explicit_refs_query_annotation_system_filter(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE_1",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_1.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "annotations": [{
                "explicit_reference" : "EXPLICIT_REFERENCE_1",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM_1"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": []
                    }]
                }]
            },{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE_2",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_2.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "annotations": [{
                "explicit_reference" : "EXPLICIT_REFERENCE_2",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM_1"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": []
                    }]
                },{
                "explicit_reference" : "EXPLICIT_REFERENCE_2",
                "annotation_cnf": {
                    "name": "NAME_2",
                    "system": "SYSTEM_2"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": []
                    }]
                }]
            }]
        }

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## Like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # Fill the annotation_system_like input
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[1]/div[2]/input")
        inputElement.send_keys("SYSTEM_2")

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 1 and empty_element is False

        ## Not like ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # find the element that's name attribute is gauge_system_like
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[1]/div[2]/input")
        inputElement.send_keys("SYSTEM_2")

        notLikeButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[1]/div[2]/label")
        if not notLikeButton.find_element_by_xpath("input").is_selected():
            notLikeButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 2

        ## In ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # find the element that's name attribute is gauge_system_in
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[2]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("SYSTEM_1")
        inputElement.send_keys(Keys.RETURN)

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generated
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        assert number_of_elements == 2

        ## Not in ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        # find the element that's name attribute is gauge_system_in
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[2]/div[2]/div/ul/li/input")
        inputElement.click()
        inputElement.send_keys("SYSTEM_2")
        inputElement.send_keys(Keys.RETURN)

        notInButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[4]/div[2]/div[2]/div[2]/div[2]/label")
        if not notInButton.find_element_by_xpath("input").is_selected():
            notInButton.click()
        #end if

        # Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[4]/div/div/div/div/div/form/div[7]/button')))
        submitButton.click()

        # Check table generate
        explicit_ref_table = wait.until(EC.visibility_of_element_located((By.ID,"DataTables_Table_0")))
        number_of_elements = len(explicit_ref_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(explicit_ref_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 2

    def test_explicit_refs_query_ingestion_time(self):

        # Insert data
        data = {"operations":[{
                        "mode": "insert",
                        "dim_signature": {"name": "dim_signature",
                                          "exec": "exec",
                                          "version": "1.0"},
                        "source": {"name": "source.xml",
                                   "generation_time": "2018-07-05T02:07:03",
                                   "validity_start": "2018-06-05T02:07:03",
                                   "validity_stop": "2018-06-05T08:07:36"},
                        "explicit_references": [{
                            "group": "EXPL_GROUP_1",
                            "name": "EXPLICIT_REFERENCE_1"
                            }]
                    }]
                }

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        ingestion_time = self.session.query(ExplicitRef).all()[0].ingestion_time.isoformat()

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## == ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.value_comparer(driver, wait, "explicit_refs", "ingestion_time", ingestion_time, None, True, "==")

        assert number_of_elements == 1 and empty_element is False

        ## > ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.value_comparer(driver, wait, "explicit_refs", "ingestion_time", ingestion_time, None, True, ">")

        assert empty_element is True

        ## >= ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.value_comparer(driver, wait, "explicit_refs", "ingestion_time", ingestion_time, None, True, ">=")

        assert number_of_elements == 1 and empty_element is False

        ## < ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.value_comparer(driver, wait, "explicit_refs", "ingestion_time", ingestion_time, None, True, "<")

        assert empty_element is True

        ## <= ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.value_comparer(driver, wait, "explicit_refs", "ingestion_time", ingestion_time, None, True, "<=")

        assert number_of_elements == 1 and empty_element is False

        ## != ##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.value_comparer(driver, wait, "explicit_refs", "ingestion_time", ingestion_time, None, True, "!=")

        assert empty_element is True

    def test_explicit_refs_query_period(self):

        # Insert data
        data = {"operations": [{
            "mode": "insert",
            "dim_signature": {
                  "name": "DIM_SIGNATURE_1",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_1.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T00:00:00",
                           "validity_stop": "2018-06-05T08:00:00"},
            "events": [{"gauge": {"name": "GAUGE_NAME",
                                  "system": "GAUGE_SYSTEM",
                                  "insertion_type": "SIMPLE_UPDATE"},
                        "explicit_reference": "EXPLICIT_REFERENCE_EVENT_1",
                        "start": "2018-06-05T02:00:00",
                        "stop": "2018-06-05T03:00:00",
                        "values": [{"name": "VALUES",
                                   "type": "object",
                                   "values": [
                                       {"name": "text_name_1",
                                        "type": "text",
                                        "value": "text_value_1"
                                       }]
                                   }]
                    },{"gauge": {"name": "GAUGE_NAME_2",
                                  "system": "GAUGE_SYSTEM_2",
                                  "insertion_type": "SIMPLE_UPDATE"},
                        "explicit_reference": "EXPLICIT_REFERENCE_EVENT_2",
                        "start": "2018-06-05T03:00:00",
                        "stop": "2018-06-05T04:00:00",
                        "values": [{"name": "VALUES",
                                   "type": "object",
                                   "values": [
                                       {"name": "text_name_2",
                                        "type": "text",
                                        "value": "text_value_2"
                                       }]
                                   }]
                    },{"gauge": {"name": "GAUGE_NAME_3",
                                  "system": "GAUGE_SYSTEM_3",
                                  "insertion_type": "SIMPLE_UPDATE"},
                        "explicit_reference": "EXPLICIT_REFERENCE_EVENT_3",
                        "start": "2018-06-05T04:00:00",
                        "stop": "2018-06-05T05:00:00",
                        "values": [{"name": "VALUES",
                                   "type": "object",
                                   "values": [
                                       {"name": "text_name_3",
                                        "type": "text",
                                        "value": "text_value_3"
                                       }]
                                   }]
                    }]
            }]
        }

        # Check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        ## == ## Full period##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.period_comparer(driver, wait, "explicit_refs", "2018-06-05T03:00:00", "==","2018-06-05T04:00:00", "==")

        assert number_of_elements == 1 and empty_element is False

        ## >= ## Only Start##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.period_comparer(driver, wait, "explicit_refs", start_value = "2018-06-05T03:00:00", start_operator = ">=")

        assert number_of_elements == 2

        ## != ## Only End##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.period_comparer(driver, wait, "explicit_refs", end_value = "2018-06-05T04:00:00", end_operator = "!=")

        assert number_of_elements == 2

        ## > ## Only Start## < ## Only Start##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.two_periods_comparer(driver, wait, "explicit_refs", start_value_1 = "2018-06-05T01:30:00", start_operator_1 = ">", start_value_2 = "2018-06-05T03:00:00", start_operator_2 = "<")

        assert number_of_elements == 1 and empty_element is False

        ## <= ## Start## > ## End## != ## Start## >= ## End##
        driver.get("http://localhost:5000/eboa_nav/")

        # Go to tab
        functions.goToTab(driver,"Explicit references")

        number_of_elements, empty_element =  functions.two_periods_comparer(driver, wait, "explicit_refs", start_value_1 = "2018-06-05T03:00:00", start_operator_1 = "<=", end_value_1 = "2018-06-05T02:30:00", end_operator_1 = ">",
        start_value_2 = "2018-06-05T04:00:00", start_operator_2 = "!=", end_value_2 = "2018-06-05T03:00:00", end_operator_2 = ">=")

        assert number_of_elements == 2

        driver.quit()

        assert True
