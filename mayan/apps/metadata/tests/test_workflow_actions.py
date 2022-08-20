from mayan.apps.document_states.events import event_workflow_edited
from mayan.apps.document_states.permissions import permission_workflow_edit
from mayan.apps.document_states.tests.mixins import (
    WorkflowTestMixin, WorkflowStateActionViewTestMixin
)
from mayan.apps.documents.tests.base import GenericDocumentViewTestCase
from mayan.apps.events.tests.mixins import EventTestCaseMixin

from ..events import (
    event_document_metadata_added, event_document_metadata_edited,
    event_document_metadata_removed
)
from ..models import MetadataType
from ..workflow_actions import (
    DocumentMetadataAddAction, DocumentMetadataEditAction,
    DocumentMetadataRemoveAction
)
from ..permissions import (
    permission_document_metadata_add, permission_document_metadata_edit,
    permission_document_metadata_remove
)

from .literals import (
    DOCUMENT_METADATA_ADD_ACTION_CLASS_PATH,
    DOCUMENT_METADATA_EDIT_ACTION_CLASS_PATH,
    DOCUMENT_METADATA_REMOVE_ACTION_CLASS_PATH, TEST_METADATA_VALUE,
    TEST_METADATA_VALUE_EDITED
)
from .mixins import DocumentMetadataMixin, MetadataTypeTestMixin


class DocumentMetadataActionTestCase(
    DocumentMetadataMixin, EventTestCaseMixin, MetadataTypeTestMixin,
    GenericDocumentViewTestCase
):
    auto_upload_test_document = False

    def setUp(self):
        super().setUp()
        self._create_test_document_stub()
        self._create_test_metadata_type()
        self.test_document_type.metadata.create(
            metadata_type=self.test_metadata_type
        )

    def test_document_metadata_add_action(self):
        action = DocumentMetadataAddAction(
            form_data={'metadata_types': MetadataType.objects.all()}
        )

        metadata_count = self.test_document.metadata.count()

        self._clear_events()

        action.execute(context={'document': self.test_document})

        self.assertEqual(
            self.test_document.metadata.count(), metadata_count + 1
        )
        self.assertTrue(
            self.test_document.metadata.filter(
                metadata_type=self.test_metadata_type
            ).exists()
        )

        events = self._get_test_events()
        self.assertEqual(events.count(), 1)

        self.assertEqual(events[0].action_object, self.test_metadata_type)
        self.assertEqual(events[0].actor, self.test_document)
        self.assertEqual(events[0].target, self.test_document)
        self.assertEqual(events[0].verb, event_document_metadata_added.id)

    def test_document_metadata_edit_action(self):
        self._create_test_document_metadata()

        action = DocumentMetadataEditAction(
            form_data={
                'metadata_type': self.test_metadata_type.pk,
                'value': TEST_METADATA_VALUE_EDITED
            }
        )

        metadata_value = self.test_document.metadata.first().value

        self._clear_events()

        action.execute(context={'document': self.test_document})

        self.assertNotEqual(
            metadata_value, self.test_document.metadata.first().value
        )

        events = self._get_test_events()
        self.assertEqual(events.count(), 1)

        self.assertEqual(events[0].action_object, self.test_metadata_type)
        self.assertEqual(events[0].actor, self.test_document)
        self.assertEqual(events[0].target, self.test_document)
        self.assertEqual(events[0].verb, event_document_metadata_edited.id)

    def test_document_metadata_remove_action(self):
        self._create_test_document_metadata()

        action = DocumentMetadataRemoveAction(
            form_data={'metadata_types': MetadataType.objects.all()}
        )

        metadata_count = self.test_document.metadata.count()

        self._clear_events()

        action.execute(context={'document': self.test_document})

        self.assertEqual(
            self.test_document.metadata.count(), metadata_count - 1
        )
        self.assertFalse(
            self.test_document.metadata.filter(
                metadata_type=self.test_metadata_type
            ).exists()
        )

        events = self._get_test_events()
        self.assertEqual(events.count(), 1)

        self.assertEqual(events[0].action_object, self.test_metadata_type)
        self.assertEqual(events[0].actor, self.test_document)
        self.assertEqual(events[0].target, self.test_document)
        self.assertEqual(events[0].verb, event_document_metadata_removed.id)


class DocumentMetadataActionViewTestCase(
    DocumentMetadataMixin, EventTestCaseMixin, MetadataTypeTestMixin,
    WorkflowStateActionViewTestMixin, WorkflowTestMixin,
    GenericDocumentViewTestCase
):
    auto_upload_test_document = False

    def setUp(self):
        super().setUp()
        self._create_test_document_stub()
        self._create_test_workflow()
        self._create_test_workflow_state()
        self._create_test_metadata_type()
        self.test_document_type.metadata.create(
            metadata_type=self.test_metadata_type
        )
        self.test_workflow.document_types.add(
            self.test_document_type
        )

    def test_document_metadata_add_action_create_view(self):
        self.grant_access(
            obj=self.test_workflow, permission=permission_workflow_edit
        )
        self.grant_access(
            obj=self.test_metadata_type,
            permission=permission_document_metadata_add
        )

        self._clear_events()

        response = self._request_test_workflow_template_state_action_create_post_view(
            class_path=DOCUMENT_METADATA_ADD_ACTION_CLASS_PATH, extra_data={
                'metadata_types': self.test_metadata_type.pk
            }
        )
        self.assertEqual(response.status_code, 302)

        events = self._get_test_events()
        self.assertEqual(events.count(), 1)

        self.assertEqual(
            events[0].action_object,
            self._test_workflow_template_state_action
        )
        self.assertEqual(events[0].actor, self._test_case_user)
        self.assertEqual(events[0].target, self.test_workflow)
        self.assertEqual(events[0].verb, event_workflow_edited.id)

    def test_document_metadata_edit_action_create_view(self):
        self._create_test_document_metadata()

        self.grant_access(
            obj=self.test_workflow, permission=permission_workflow_edit
        )
        self.grant_access(
            obj=self.test_metadata_type,
            permission=permission_document_metadata_edit
        )

        self._clear_events()

        response = self._request_test_workflow_template_state_action_create_post_view(
            class_path=DOCUMENT_METADATA_EDIT_ACTION_CLASS_PATH, extra_data={
                'metadata_type': self.test_metadata_type.pk,
                'value': TEST_METADATA_VALUE
            }
        )
        self.assertEqual(response.status_code, 302)

        events = self._get_test_events()
        self.assertEqual(events.count(), 1)

        self.assertEqual(
            events[0].action_object,
            self._test_workflow_template_state_action
        )
        self.assertEqual(events[0].actor, self._test_case_user)
        self.assertEqual(events[0].target, self.test_workflow)
        self.assertEqual(events[0].verb, event_workflow_edited.id)

    def test_document_metadata_remove_action_create_view(self):
        self._create_test_document_metadata()

        self.grant_access(
            obj=self.test_workflow, permission=permission_workflow_edit
        )
        self.grant_access(
            obj=self.test_metadata_type,
            permission=permission_document_metadata_remove
        )

        self._clear_events()

        response = self._request_test_workflow_template_state_action_create_post_view(
            class_path=DOCUMENT_METADATA_REMOVE_ACTION_CLASS_PATH,
            extra_data={
                'metadata_types': self.test_metadata_type.pk
            }
        )
        self.assertEqual(response.status_code, 302)

        events = self._get_test_events()
        self.assertEqual(events.count(), 1)

        self.assertEqual(
            events[0].action_object,
            self._test_workflow_template_state_action
        )
        self.assertEqual(events[0].actor, self._test_case_user)
        self.assertEqual(events[0].target, self.test_workflow)
        self.assertEqual(events[0].verb, event_workflow_edited.id)
