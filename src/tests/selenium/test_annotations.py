"""
Automated tests for the annotations tab

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

    def test_annotations_query_no_filter_no_map(self):

        #insert data
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
            "annotations": [{
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
            }]}

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        #Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[9]/button')))
        submitButton.click()

        #Check table generated
        annot_table = wait.until(EC.visibility_of_element_located((By.ID,"annotations")))
        number_of_elements = len(annot_table.find_elements_by_xpath("tbody/tr"))

        driver.quit()

        assert number_of_elements == 2

    def test_annotations_query_no_filter_with_map(self):

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        #Click on show map
        mapButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[8]/label")
        if not mapButton.is_selected():
            mapButton.click()

        #Apply filters and click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[9]/button')))
        submitButton.click()

        map = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div[3]/div[2]/div/div")

        map.screenshot("map_screenshot.png")

        condition = map.is_displayed()

        driver.quit()

        return condition

    def test_annotations_query_source_like_filter_no_map(self):

        #insert data
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
            "annotations": [{
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
                  "name": "DIM_SIGNATURE",
                  "exec": "exec",
                  "version": "1.0"
            },
            "source":  {"name": "source_2.xml",
                           "generation_time": "2018-07-05T02:07:03",
                           "validity_start": "2018-06-05T02:07:03",
                           "validity_stop": "2018-06-05T08:07:36"},
            "annotations": [{
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
            }
        ]}

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        # find the element that's name attribute is source_like
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[1]/div[1]/input")
        inputElement.send_keys("source_1.xml")

        #Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[9]/button')))
        submitButton.click()

        #Check table generated
        annot_table = wait.until(EC.visibility_of_element_located((By.ID,"annotations")))
        number_of_elements = len(annot_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(annot_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 1 and empty_element is False

    def test_annotations_query_source_not_like_filter_no_map(self):

        #insert data
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        notLikeButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[1]/div[1]/label")
        if not notLikeButton.is_selected():
            notLikeButton.click()

        # find the element that's name attribute is source_not_like
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[1]/div[1]/input")
        inputElement.send_keys("source_1.xml")

        #Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[9]/button')))
        submitButton.click()

        #Check table generated
        annot_table = wait.until(EC.visibility_of_element_located((By.ID,"annotations")))
        number_of_elements = len(annot_table.find_elements_by_xpath("tbody/tr"))

        driver.quit()

        assert number_of_elements == 2

    def test_annotations_query_source_in_filter_no_map(self):

        #insert data
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        # find the element that's name attribute is source_in
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[1]/div[1]/input")
        inputElement.send_keys("source_2.xml")

        #Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[9]/button')))
        submitButton.click()

        #Check table generated
        annot_table = wait.until(EC.visibility_of_element_located((By.ID,"annotations")))
        number_of_elements = len(annot_table.find_elements_by_xpath("tbody/tr"))

        driver.quit()

        assert number_of_elements == 2

    def test_annotations_query_source_not_in_filter_no_map(self):

        #insert data
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        notInButton = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[1]/div[2]/label")
        if not notInButton.is_selected():
            notInButton.click()

        # find the element that's name attribute is source_not_in
        inputElement = driver.find_element_by_xpath("/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[1]/div[2]/div/ul/li/input")
        inputElement.send_keys("source_1.xml")
        inputElement.send_keys(Keys.RETURN)

        #Click on query button
        submitButton = wait.until(EC.visibility_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div/div[2]/div/div/div/div/div/form/div[9]/button')))
        submitButton.click()

        #Check table generated
        annot_table = wait.until(EC.visibility_of_element_located((By.ID,"annotations")))
        number_of_elements = len(annot_table.find_elements_by_xpath("tbody/tr"))
        empty_element = len(annot_table.find_elements_by_xpath("tbody/tr/td[contains(@class,'dataTables_empty')]")) > 0

        driver.quit()

        assert number_of_elements == 2

    def test_annotations_query_value_text(self):

        #insert data
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": [
                        {"name": "text_name_1",
                         "type": "text",
                         "value": "text_value_1"
                        }]
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values":  [
                    {"name": "text_name_2",
                     "type": "text",
                     "value": "text_value_2"
                        }]
                    }]
                },{
                "explicit_reference" : "EXPLICIT_REFERENCE",
                "annotation_cnf": {
                    "name": "NAME_2",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": [
                        {"name": "text_name_3",
                         "type": "text",
                         "value": "text_value_2"
                        }]
                    }]
                }]
            }]
        }

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "text", "text_name_1", "text_value_1", True, "==")

        assert number_of_elements == 1 and empty_element is False

        #Not like
        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "text", "text_name_1", "text_value_2", False, "==")

        driver.quit()

        assert  number_of_elements == 2

    def test_annotations_query_value_timestamp(self):

        #insert data
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": [
                        {"name": "timestamp_name_1",
                         "type": "timestamp",
                         "value": "2019-04-26T14:14:14"
                        }]
                    }]
                }]
            }]
        }

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:14", True, "==")

        assert number_of_elements == 1 and empty_element is False

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:20", True, "==")

        assert empty_element is True

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:14", True, ">")

        assert empty_element is True

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:10", True, ">")

        assert number_of_elements == 1 and empty_element is False

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:20", True, ">")

        assert empty_element == True

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:14", True, ">=")

        assert number_of_elements == 1 and empty_element is False

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:10", True, ">=")

        assert number_of_elements == 1 and empty_element is False

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:20", True, ">=")

        assert empty_element == True

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:14", True, "<")

        assert empty_element is True

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:10", True, "<")

        assert empty_element is True

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:20", True, "<")

        assert number_of_elements == 1 and empty_element is False

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:14", True, "<=")

        assert number_of_elements == 1 and empty_element is False

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:10", True, "<=")

        assert empty_element is True

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:20", True, "<=")

        assert number_of_elements == 1 and empty_element is False

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:14", True, "!=")

        assert empty_element is True

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:10", True, "!=")

        assert number_of_elements == 1 and empty_element is False

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element = functions.annotations_value_comparer(driver, wait, "timestamp", "timestamp_name_1", "2019-04-26T14:14:20", True, "!=")

        driver.quit()

        assert number_of_elements == 1 and empty_element is False

    def test_annotations_query_ingestion_time(self):

        #insert data
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
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
            }]
        }

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        ingestion_time = self.session.query(Annotation).all()[0].ingestion_time.isoformat()

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element =  functions.annotations_value_comparer(driver, wait, "ingestion_time", ingestion_time, None, True, "==")

        assert number_of_elements == 1 and empty_element is False

        #>
        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element =  functions.annotations_value_comparer(driver, wait, "ingestion_time", ingestion_time, None, True, ">")

        assert empty_element is True

        #>=
        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element =  functions.annotations_value_comparer(driver, wait, "ingestion_time", ingestion_time, None, True, ">=")

        assert number_of_elements == 1 and empty_element is False

        #<
        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element =  functions.annotations_value_comparer(driver, wait, "ingestion_time", ingestion_time, None, True, "<")

        assert empty_element is True

        #<=
        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element =  functions.annotations_value_comparer(driver, wait, "ingestion_time", ingestion_time, None, True, "<=")

        assert number_of_elements == 1 and empty_element is False

        #!=
        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element =  functions.annotations_value_comparer(driver, wait, "ingestion_time", ingestion_time, None, True, "!=")

        assert empty_element is True

    def test_annotations_query_two_values(self):

        #insert data
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": [
                        {"name": "text_name_1",
                         "type": "text",
                         "value": "text_value_1"
                        }]
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
                "explicit_reference" : "EXPLICIT_REFERENCE",
                "annotation_cnf": {
                    "name": "NAME_1",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values":  [
                    {"name": "text_name_1",
                     "type": "text",
                     "value": "text_value_1"
                        },
                    {"name": "double_name_1",
                     "type": "double",
                     "value": "1.4"
                        }]
                    }]
                },{
                "explicit_reference" : "EXPLICIT_REFERENCE",
                "annotation_cnf": {
                    "name": "NAME_2",
                    "system": "SYSTEM"
                    },
                "values": [{
                    "name": "details",
                    "type": "object",
                    "values": [
                        {"name": "text_name_3",
                         "type": "text",
                         "value": "text_value_2"
                        }]
                    }]
                }]
            }]
        }

        #check data is correctly inserted
        self.engine_eboa.data = data
        assert eboa_engine.exit_codes["OK"]["status"] == self.engine_eboa.treat_data()[0]["status"]

        # Create a new instance of the Firefox driver
        driver = webdriver.Firefox(options=self.options)

        wait = WebDriverWait(driver,30);

        driver.get("http://localhost:5000/eboa_nav/")

        #Go to tab
        functions.goToTab(driver,"Annotations")

        number_of_elements, empty_element =  functions.annotations_two_values_comparer(driver, wait, "text", "double", "text_name_1", "text_value_1", "double_name_1", "1.4", True, True, "==", "==")

        assert number_of_elements == 1 and empty_element is False

        driver.quit()

        assert True
