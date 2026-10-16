"""Expose the KFV suite to the project's existing test commands."""
from importlib import import_module


StandardsCatalogTests = import_module(
	"projects-kfv.tests.test_standards_catalog"
).StandardsCatalogTests