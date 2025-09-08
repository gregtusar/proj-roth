import React, { useState } from 'react';
import { styled } from 'baseui';
import { Button } from 'baseui/button';
import { Textarea } from 'baseui/textarea';
import { Select } from 'baseui/select';
import { Pagination } from 'baseui/pagination';
import { Plus } from 'baseui/icon';
import { toaster } from 'baseui/toast';
import axios from 'axios';

const Container = styled('div', {
  padding: '24px',
});

const AddEventSection = styled('div', ({ $theme }) => ({
  marginBottom: '32px',
  padding: '20px',
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  border: `1px solid ${$theme.colors.borderOpaque}`,
}));

const SectionTitle = styled('h3', ({ $theme }) => ({
  fontSize: '18px',
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
  marginBottom: '16px',
}));

const FormGroup = styled('div', {
  marginBottom: '16px',
});

const FormLabel = styled('label', ({ $theme }) => ({
  display: 'block',
  fontSize: '14px',
  fontWeight: 500,
  color: $theme.colors.contentPrimary,
  marginBottom: '8px',
}));

const ButtonGroup = styled('div', {
  display: 'flex',
  gap: '12px',
  marginTop: '16px',
});

const EventsList = styled('div', ({ $theme }) => ({
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  overflow: 'hidden',
  maxHeight: '600px',
  overflowY: 'auto',
}));

const PaginationContainer = styled('div', {
  display: 'flex',
  justifyContent: 'center',
  marginTop: '20px',
});

const EventItem = styled('div', ({ $theme }) => ({
  padding: '16px',
  borderBottom: `1px solid ${$theme.colors.borderOpaque}`,
  ':last-child': {
    borderBottom: 'none',
  },
}));

const EventHeader = styled('div', {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
  marginBottom: '8px',
});

const EventType = styled('div', ({ $theme }) => ({
  fontSize: '14px',
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
  padding: '4px 8px',
  backgroundColor: $theme.colors.backgroundTertiary,
  borderRadius: '4px',
  display: 'inline-block',
}));

const EventDate = styled('div', ({ $theme }) => ({
  fontSize: '12px',
  color: $theme.colors.contentSecondary,
}));

const EventNotes = styled('div', ({ $theme }) => ({
  fontSize: '14px',
  color: $theme.colors.contentPrimary,
  lineHeight: 1.6,
  whiteSpace: 'pre-wrap',
}));

const EventMeta = styled('div', ({ $theme }) => ({
  marginTop: '8px',
  fontSize: '12px',
  color: $theme.colors.contentSecondary,
}));

const NoEventsMessage = styled('div', ({ $theme }) => ({
  padding: '24px',
  textAlign: 'center',
  color: $theme.colors.contentSecondary,
  fontSize: '14px',
}));

interface EventsSectionProps {
  events: any[];
  masterId: string;
  onEventAdded: (event: any) => void;
}

const EventsSection: React.FC<EventsSectionProps> = ({ events, masterId, onEventAdded }) => {
  const [isAddingEvent, setIsAddingEvent] = useState(false);
  const [eventType, setEventType] = useState<any>([{ id: 'call_notes', label: 'Call Notes' }]);
  const [eventNotes, setEventNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const eventsPerPage = 10;

  const eventTypeOptions = [
    { id: 'call_notes', label: 'Call Notes' },
    { id: 'meeting', label: 'Meeting' },
    { id: 'email', label: 'Email' },
    { id: 'door_knock', label: 'Door Knock' },
    { id: 'event_attendance', label: 'Event Attendance' },
    { id: 'volunteer', label: 'Volunteer Activity' },
    { id: 'donation', label: 'Donation' },
    { id: 'other', label: 'Other' },
  ];

  const handleSaveEvent = async () => {
    if (!eventNotes.trim()) {
      toaster.warning('Please enter event notes');
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post(
        '/api/crm/events',
        {
          voter_master_id: masterId,
          event_type: eventType[0]?.id || 'call_notes',
          notes: eventNotes.trim(),
          metadata: {},
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      onEventAdded(response.data);
      setEventNotes('');
      setIsAddingEvent(false);
      toaster.positive('Event saved successfully');
    } catch (error) {
      console.error('Error saving event:', error);
      toaster.negative('Failed to save event');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatEventDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getEventTypeLabel = (type: string) => {
    const option = eventTypeOptions.find(opt => opt.id === type);
    return option?.label || type;
  };

  return (
    <Container>
      <AddEventSection>
        <SectionTitle>Add New Event</SectionTitle>
        
        {!isAddingEvent ? (
          <Button
            onClick={() => setIsAddingEvent(true)}
            startEnhancer={<Plus size={20} />}
            kind="secondary"
          >
            Add Event
          </Button>
        ) : (
          <>
            <FormGroup>
              <FormLabel>Event Type</FormLabel>
              <Select
                options={eventTypeOptions}
                value={eventType}
                onChange={({ value }) => setEventType(value)}
                placeholder="Select event type"
              />
            </FormGroup>
            
            <FormGroup>
              <FormLabel>Notes</FormLabel>
              <Textarea
                value={eventNotes}
                onChange={(e) => setEventNotes(e.currentTarget.value)}
                placeholder="Enter event notes, call details, or other relevant information..."
                rows={4}
              />
            </FormGroup>
            
            <ButtonGroup>
              <Button
                onClick={handleSaveEvent}
                isLoading={isSubmitting}
                disabled={!eventNotes.trim()}
              >
                Save Event
              </Button>
              <Button
                onClick={() => {
                  setIsAddingEvent(false);
                  setEventNotes('');
                }}
                kind="secondary"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </ButtonGroup>
          </>
        )}
      </AddEventSection>

      <div>
        <SectionTitle>Event History</SectionTitle>
        {events && events.length > 0 ? (
          <>
            <EventsList>
              {events
                .slice((currentPage - 1) * eventsPerPage, currentPage * eventsPerPage)
                .map((event) => (
                  <EventItem key={event.event_id}>
                    <EventHeader>
                      <EventType>{getEventTypeLabel(event.event_type)}</EventType>
                      <EventDate>{formatEventDate(event.created_at)}</EventDate>
                    </EventHeader>
                    <EventNotes>{event.notes}</EventNotes>
                    <EventMeta>
                      Created by: {event.created_by || 'Unknown'}
                      {event.metadata && event.metadata.campaign_name && (
                        <> • Campaign: {event.metadata.campaign_name}</>
                      )}
                    </EventMeta>
                  </EventItem>
                ))}
            </EventsList>
            {events.length > eventsPerPage && (
              <PaginationContainer>
                <Pagination
                  numPages={Math.ceil(events.length / eventsPerPage)}
                  currentPage={currentPage}
                  onPageChange={({ nextPage }) => {
                    setCurrentPage(Math.min(Math.max(nextPage, 1), Math.ceil(events.length / eventsPerPage)));
                  }}
                />
              </PaginationContainer>
            )}
          </>
        ) : (
          <NoEventsMessage>No events recorded for this voter</NoEventsMessage>
        )}
      </div>
    </Container>
  );
};

export default EventsSection;